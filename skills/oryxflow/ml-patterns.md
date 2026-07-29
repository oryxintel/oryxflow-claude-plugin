# oryxflow ML Pipeline Patterns

Concrete, copy-adaptable task templates for machine-learning pipelines built with
oryxflow. Loaded ON DEMAND by the `oryxflow` skill - pull this in only when the work
is ML (feature engineering, model training, backtesting, predictions). For the
general library reference see [reference.md](reference.md); for the essentials see
[SKILL.md](SKILL.md).

The task templates below carry no `code_version`, which is correct: auto
invalidation (oryxflow >= 26.7.12, on by default) reruns an edited task on its
own. `code_version` is an opt-in LOCK you add only to pin an EXPENSIVE task
(`ModelTrain`, a long backtest) so it recomputes on a deliberate bump instead of
on any refactor - which pairs naturally with the frozen-model prod pattern below.
See SKILL.md "Code-aware invalidation".

## ML pipeline architecture

Standard pipeline structure:

```
Data loading -> Feature engineering -> Model training -> Evaluation -> Predictions
```

Typical task sequence:

```
FeaturesRaw -> FeaturesTransform -> ModelTrain -> ModelPerformanceIS
            -> ModelPredictOS -> ModelPredictCurrent
```

---

## Core principles

### 1. Data structure requirements

Define grouping columns in `cfg.py`:

```python
cfg.col_g_entity = ['sector', 'id']               # Entity identifiers
cfg.col_g_time = ['date']                          # Time column
cfg.col_g_entity_time = ['sector', 'id', 'date']   # Combined
```

### 2. Feature organization

Organize features by type in `cfg.py`:

```python
cfg.col_X = ['feature1', 'feature2', ...]      # All features
cfg.col_X_rate = ['unemployment_rate', ...]    # Rate features (use diff, not pct_change)
cfg.col_X_level = ['gdp', 'price', ...]        # Level features (use pct_change)
```

### 3. Multiple output pattern

Use `persists` to name a task's multiple outputs:

```python
class MyTask(oryxflow.tasks.TaskPqPandas):
    persists = ['all', 'x', 'y']  # output names (persist is a legacy alias)

    def run(self):
        self.save([df_all, df_X, df_y], from_list=True)  # list: positional by order
        # or: self.save({'all': df_all, 'x': df_X, 'y': df_y})  # dict: by name
```

The output names live in `persists`. Whether you pass a list or a dict to
`save()` is what selects positional-vs-by-name saving - not the attribute. The
list form needs `from_list=True`; the dict keys must match `persists`.

Load multiple outputs:

```python
df_all, df_X, df_y = self.inputLoad()
```

### 4. Metadata pattern

Store models and non-DataFrame objects in metadata:

```python
# Save
self.save(df)
self.saveMeta({'model': model, 'config': {...}})

# Load
df = self.inputLoad()
meta = self.metaLoad(key=0)  # key=0 for first dependency
model = meta['model']
```

---

## Pattern 1: Feature engineering

### FeaturesRaw - merge data sources

Purpose: merge multiple data sources, create derived features.

```python
@oryxflow.requires(DataSource1, DataSource2)
class FeaturesRaw(oryxflow.tasks.TaskPqPandas):
    """Merge data sources and create base features"""

    def run(self):
        df_primary, df_secondary = self.inputLoad()

        # Filter to relevant subset (if needed)
        df_primary = df_primary[df_primary['sector'] == self.sector]

        # Merge on key columns
        df_merged = df_primary.merge(
            df_secondary,
            on=['entity_id', 'date'],  # Adjust to your keys
            how='left'
        )

        # Validate merge
        assert df_merged.shape[0] <= df_primary.shape[0], "Merge created duplicates"
        assert df_merged.shape[0] >= df_primary.shape[0] * 0.9, "Lost >10% of rows"

        self.save(df_merged)
```

Key concepts: merge on entity + time keys; validate no duplicates and minimal data
loss; use `how='left'` to preserve the primary dataset.

### FeaturesTransform - transform for modeling

Purpose: transform features (normalize, rank, time-series features), split X/y.

```python
@oryxflow.requires(FeaturesRaw)
class FeaturesTransform(oryxflow.tasks.TaskPqPandas):
    """Transform features for modeling"""
    transformx = oryxflow.Parameter()  # Feature transformation method
    transformy = oryxflow.Parameter()  # Target transformation
    persists = ['all', 'x', 'y']

    def run(self):
        df = self.inputLoad()
        df = df.sort_values(['entity_id', 'date'])  # Adjust to your columns

        # Transform features and target
        df_X = self.transform_features(df)
        df_y = self.transform_target(df)

        # Handle missing values
        df_X = df_X.dropna()
        assert df_X.shape[0] / df.shape[0] > 0.8, \
            f"Dropped {100*(1-df_X.shape[0]/df.shape[0]):.1f}% of data"
        self.logger.info("kept {} rows ({} feats); dropped {:.1f}% on dropna",
                         len(df_X), df_X.shape[1], 100*(1 - df_X.shape[0]/df.shape[0]))

        # Keep only rows with valid features
        df = df.loc[df_X.index]
        df_y = df_y.loc[df_X.index]
        df['y'] = df_y.values

        self.save([df, df_X, df_y], from_list=True)

    def transform_features(self, df):
        """Apply feature transformation based on transformx parameter"""
        if self.transformx == 'raw':
            return df[cfg.col_X].copy()
        elif self.transformx == 'normalized':
            df_X = df[cfg.col_X].copy()
            return (df_X - df_X.mean()) / df_X.std()       # Z-score
        elif self.transformx == 'rank':
            df_X = df[cfg.col_X].copy()
            for col in cfg.col_X:
                df_X[col] = df.groupby('date')[col].rank(pct=True)  # Cross-sectional
            return df_X
        else:
            raise NotImplementedError(f"transformx={self.transformx}")

    def transform_target(self, df):
        """Apply target transformation based on transformy parameter"""
        if self.transformy == 'raw':
            return df['target']
        elif self.transformy == 'rank':
            return df.groupby('date')['target'].rank(pct=True)
        else:
            raise NotImplementedError(f"transformy={self.transformy}")
```

Common transformations: `raw` (as-is), `normalized` (z-score), `rank`
(cross-sectional percentile, 0-1), `log` (skewed data). Critical steps: sort by
entity + time first; transform features and target separately; drop NaN after
transformations and validate <20% loss; return `[df_all, df_X, df_y]`.

---

## Pattern 2: Model training

### ModelTrain - train ML model

Purpose: train model, save the model object in metadata, calculate SHAP values.

```python
@oryxflow.requires(FeaturesTransform)
class ModelTrain(oryxflow.tasks.TaskPqPandas):
    """Train ML model and save predictions"""
    model = oryxflow.Parameter()  # Model type
    persists = ['all', 'x', 'y']

    def run(self):
        df_all, df_X, df_y = self.inputLoad()

        # Exclude rows with missing targets
        idxSel = df_all['target'].notna()
        df_all, df_X, df_y = df_all[idxSel], df_X[idxSel], df_y[idxSel]

        # Train model
        model = self.train_model(df_X, df_y)
        self.logger.info("trained {} on {} rows, {} feats", self.model, len(df_X), df_X.shape[1])

        # Add predictions to dataset
        df_all['y_pred'] = model.predict(df_X)

        # Calculate SHAP for tree models
        meta = {'model': model}
        if self.model in ['lgbm', 'rf', 'xgb']:
            import shap
            meta['shap-explainer'] = shap.Explainer(model, df_X)

        self.save([df_all, df_X, df_y], from_list=True)
        self.saveMeta(meta)

    def train_model(self, X, y):
        """Train model based on model parameter"""
        if self.model == 'lgbm':
            import lightgbm
            return lightgbm.LGBMRegressor(random_state=42).fit(X, y)
        elif self.model == 'rf':
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(random_state=42).fit(X, y)
        elif self.model == 'ols':
            from sklearn.linear_model import LinearRegression
            return LinearRegression().fit(X, y)
        else:
            raise NotImplementedError(f"model={self.model}")
```

Critical steps: exclude missing targets before training (recent periods may not
have forward returns); save the model in metadata (not the main output); calculate
the SHAP explainer during training for tree models (reuse later); add a `y_pred`
column; always set `random_state` for reproducibility.

For classification (imbalanced data):

```python
def train_model(self, X, y):
    import lightgbm
    if self.imbalanced:
        from imblearn.over_sampling import SMOTE
        X, y = SMOTE(random_state=42).fit_resample(X, y)
    return lightgbm.LGBMClassifier(class_weight='balanced', random_state=42).fit(X, y)
```

### Comparing model variants in ONE flow (fan-out)

To score several models against each other and keep building downstream, fan out
over `model` and converge on a combining task - the shared data prep runs ONCE:

```python
@oryxflow.requires_each(ModelTrain, model=cfg.MODELS)   # one ModelTrain per model
class ModelCombine(oryxflow.tasks.TaskPqPandas):
    """Every variant's predictions in one frame, tagged with `model`."""

    def run(self):
        self.save(self.inputLoadConcat())

@oryxflow.requires(ModelCombine)                        # back to plain requires
class ModelReport(oryxflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad().assign(error=lambda d: (d['y_pred'] - d['target']).abs())
        self.save(df.groupby('model')['error'].mean().reset_index())
```

`FeaturesTransform` has no `model` parameter, so it is ONE task however many
variants you compare - add a fifth model and only that branch trains. Neither
`ModelCombine` nor anything downstream may declare `model` (that is where the
branches meet). Then `flow.reset_upstream(ModelReport, only=ModelTrain)` retrains
every variant while keeping the feature build cached. Fan out for one combined
comparison; use `WorkflowMulti` when the variants are separately managed runs
(reference.md Pattern 1). Needs oryxflow >= 26.7.28 - see
[dynamic-dags.md](dynamic-dags.md).

Fan out over more than one knob by naming more parameters -
`@oryxflow.requires_each(ModelTrain, model=cfg.MODELS, horizon=[1, 5, 20])` is the
cartesian product, and `df.groupby(['model', 'horizon'])` works on the result.

---

## Pattern 3: Model performance

### ModelPerformanceIS - in-sample metrics

Purpose: calculate performance metrics and feature importance.

```python
@oryxflow.requires(ModelTrain)
class ModelPerformanceIS(oryxflow.tasks.TaskPickle):
    """Calculate in-sample performance metrics"""

    def run(self):
        df_all, df_X, df_y = self.inputLoad()
        meta = self.metaLoad()
        model = meta['model']

        metrics = {}
        df_valid = df_all[['y', 'y_pred']].dropna()

        if self.is_regression():
            from sklearn.metrics import mean_squared_error, r2_score
            metrics['rmse'] = mean_squared_error(df_valid['y'], df_valid['y_pred'], squared=False)
            metrics['r2'] = r2_score(df_valid['y'], df_valid['y_pred'])
        else:
            from sklearn.metrics import accuracy_score, roc_auc_score
            metrics['accuracy'] = accuracy_score(df_valid['y'], df_valid['y_pred'])
            metrics['auc'] = roc_auc_score(df_valid['y'], df_valid['y_pred'])

        # Feature importance (tree models)
        if self.model in ['lgbm', 'rf', 'xgb']:
            import shap
            shap_values = shap.Explainer(model)(df_X)
            mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
            metrics['feature_importance'] = pd.DataFrame({
                'feature': df_X.columns, 'importance': mean_abs_shap
            }).sort_values('importance', ascending=False)
            metrics['shap_values'] = shap_values

        self.save(metrics)

    def is_regression(self):
        return self.model in ['lgbm', 'rf', 'ols'] and not hasattr(self, 'classification')
```

Key metrics - regression: RMSE, R2, MAE. Classification: accuracy, AUC,
precision/recall. Feature importance: mean absolute SHAP values (tree models).

---

## Pattern 4: Out-of-sample predictions

### ModelPredictOS - expanding-window backtest

Purpose: generate out-of-sample predictions using an expanding window to avoid
lookahead bias.

```python
@oryxflow.requires(ModelTrain, FeaturesTransform)
class ModelPredictOS(oryxflow.tasks.TaskPqPandas):
    """Generate out-of-sample predictions"""
    forecast_periods = oryxflow.IntParameter()  # Periods ahead to predict

    def run(self):
        (df_trainIS, _, _), (df_full, df_X_full, df_y_full) = self.inputLoad()
        model = self.metaLoad(key=0)['model']

        dates_train = sorted(df_trainIS['date'].unique())
        dates_all = sorted(df_full['date'].unique())
        min_periods = 20  # Minimum training period; adjust to data frequency

        df_full['y_pred_os'] = np.nan

        # Expanding window loop
        for train_date in dates_train[min_periods:]:
            pred_date = dates_all[dates_all.index(train_date) + self.forecast_periods]

            if train_date <= df_trainIS['date'].max():
                # Retrain on all data up to train_date
                idx_train = (df_full['date'] <= train_date) & (df_full['y'].notna())
                model.fit(df_X_full.loc[idx_train], df_y_full.loc[idx_train])

            # Predict for pred_date
            idx_pred = df_full['date'] == pred_date
            df_full.loc[idx_pred, 'y_pred_os'] = model.predict(df_X_full[idx_pred])

        self.save(df_full)
        self.saveMeta({'backtest_start': dates_train[min_periods]})
```

Critical concept - the expanding window prevents lookahead bias: train on all data
from the start to time T, predict for time T + N, never use future data for
training, and retrain for each historical period.

Alternative (rolling window, not recommended - loses data):

```python
# Train on [T-window:T], predict T+N
idx_train = (df['date'] > train_date - window) & (df['date'] <= train_date)
```

---

## Pattern 5: Current-period predictions

### ModelPredictCurrent - latest predictions

Purpose: generate predictions for the most recent period, with SHAP values.

```python
@oryxflow.requires(ModelTrain, FeaturesTransform)
class ModelPredictCurrent(oryxflow.tasks.TaskPqPandas):
    """Generate predictions for current period"""
    period_current = oryxflow.Parameter()  # e.g. '2025Q2', '2025-01-01'
    persists = ['predictions', 'features', 'shap']

    def run(self):
        _, (df_all, df_X, _) = self.inputLoad()
        meta = self.metaLoad(key=0)
        model = meta['model']

        # Filter to current period
        idx_current = df_all['date'] == self.period_current
        if idx_current.sum() == 0:
            raise RuntimeError(f'No data for period {self.period_current}')

        df_current = df_all[idx_current].copy()
        df_X_current = df_X[idx_current].copy()
        df_current['y_pred'] = model.predict(df_X_current)

        # SHAP values for interpretability
        df_shap = pd.DataFrame()
        if 'shap-explainer' in meta:
            shap_values = meta['shap-explainer'](df_X_current)
            df_shap = pd.DataFrame(
                shap_values.values, columns=df_X_current.columns, index=df_X_current.index
            )

        df_current = df_current.sort_values('y_pred', ascending=False)
        self.save({'predictions': df_current, 'features': df_X_current, 'shap': df_shap})
```

Key steps: filter to the prediction period; use the model trained on all historical
data; calculate SHAP values for interpretability; sort by prediction score.

---

## Productionizing: prod vs experiment

Once a research pipeline is trusted, it goes to "prod" - a repeatable run on
frozen settings against fresh data - while experimentation continues in the same
directory. The two coexist through three pieces:

**1. `params_prod` defined ONCE, in `flow_params.py`** (see conventions.md
"Scaling up"). The frozen production settings live in one dict; the prod
orchestration IMPORTS it rather than re-hardcoding the values inline (re-typing
them is how prod and the recorded params drift apart).

**2. A `RunAll...Prod` orchestration task** that FANS OUT over the prod variants -
one declared dependency per variant, combined into the deliverable. Its experiment
twin (`RunAll`) uses `params`.

```python
# tasks.py spine - prod orchestration
@oryxflow.requires_each(tasks_predict.ModelPredictCurrent, sector=cfg.sectors)
class RunAllModelPredictCurrentProd(oryxflow.tasks.TaskExcelPandas):
    """Prod deliverable: current predictions for every sector, one sheet.

    In:  ModelPredictCurrent, one branch per sector (frozen params_prod).
    Out: the branches stacked, each row tagged with its `sector`.
    """

    def run(self):
        self.save(self.inputLoadConcat())
```

Do NOT write this as a `for sector in cfg.sectors:` loop that builds a
`oryxflow.Workflow` per sector inside `run()`. Those tasks are not dependencies, so
the selective reset below cannot find them and silently does nothing - the prod
run then serves LAST period's numbers under this period's label, with a green run.
(See [dynamic-dags.md](dynamic-dags.md); needs oryxflow >= 26.7.28.)

**The SELECTIVE RESET is a run decision, so it lives in the entrypoint**, not
inside the task - refresh the data layers so a new period pulls fresh inputs, but
do NOT reset `ModelTrain`, so the production model stays frozen/cached across runs:

```python
# run_prod.py
from flow_params import params_prod

flow = oryxflow.Workflow(tasks.RunAllModelPredictCurrentProd,
                         params={**params_prod, 'period_current': period},
                         env='prod')
flow.reset_upstream(tasks.RunAllModelPredictCurrentProd,
                    only=tasks_features.DataSource)   # refresh data layer ONLY,
                                                      # every sector, found via the DAG
# do NOT reset ModelTrain -> frozen model stays cached
flow.run()
```

`only=` is what makes this safe at scale: it discovers every `DataSource` instance
across all sectors through the DAG, so adding a sector needs no change here.

**3. Environment-segregated outputs** via `cfg.env`, so runs under different envs
never overwrite each other's outputs. `env` is a label YOU choose, not a fixed
scheme - commonly `dev` vs `prod`, but also e.g. `utest` for a sampled subset you
can share. Pick what the project needs; don't assume prod/dev is universal.

**Periodic-refresh protocol** (the recurring prod run): refresh the raw inputs in
`data/`, bump `period_current` (in `flow_params.py` or as the prod params), then
run `run_prod.py`. Its selective reset re-pulls the data layers for the new period
while the trained model is reused as-is.

The prod run gets its own ENTRYPOINT file, `run_prod.py` (kept separate from the
experiment `run.py`) - it builds the prod Workflow inline and can either run the
`RunAll...Prod` task or inline the orchestration. This is the general "Run tiers
by lifecycle" pattern in [conventions.md](conventions.md) (copy it from the
plugin's `resources/template-prod/`); the freeze-the-model / refresh-the-data
selective reset here is that pattern's cost+authority rule in the ML case.

### Productionize a research project / notebook

Research often starts as a messy notebook - cells that load, munge, fit, and
plot in one scroll. To productionize it, sort those cells into the standard task
bins (the same ones in "Task organization checklist" below): load -> features ->
model -> eval -> predict. Each coherent cell-group becomes a TASK with a real
docstring; wire the DAG with `@oryxflow.requires(...)`; then add the prod
orchestration above.

This is the no-inline-Python rule (SKILL.md) applied to a whole notebook: code
that does pipeline work becomes a task, and a throwaway check becomes an `eda/`
probe - never a `python -c` or a cell left to rot. Once the cells are tasks, the
notebook (if kept) imports the flow and `flow.outputLoad(...)`s, like any other
report notebook.

---

## Common feature-engineering patterns

### Time-based features

Year-over-year changes:

```python
# For rates (use diff)
df['unemployment_rate_yoy'] = df.groupby('entity_id')['unemployment_rate'].diff(4)

# For levels (use pct_change)
df['gdp_yoy'] = df.groupby('entity_id')['gdp'].pct_change(4, fill_method=None)

# Clip extreme outliers
df['gdp_yoy'] = df['gdp_yoy'].clip(df['gdp_yoy'].quantile(0.01), df['gdp_yoy'].quantile(0.99))
```

Moving averages:

```python
df['price_ma_4'] = df.groupby('entity_id')['price'].transform(lambda x: x.rolling(4).mean())
df['price_ma_12'] = df.groupby('entity_id')['price'].transform(lambda x: x.rolling(12).mean())
```

Momentum features:

```python
df['momentum'] = df.groupby('entity_id')['price'].pct_change(4)
df['acceleration'] = df.groupby('entity_id')['momentum'].diff(1)
```

Forward targets (for prediction):

```python
# Simple forward shift
df['target_fwd'] = df.groupby('entity_id')['target'].shift(-forecast_periods)

# Forward CAGR (compound annual growth rate)
def calc_cagr(x, periods_per_year):
    return (1 + x).prod() ** (1 / (len(x) / periods_per_year)) - 1

df['return_cagr'] = df.groupby('entity_id')['return'].rolling(12).apply(
    lambda x: calc_cagr(x, periods_per_year=4)
).reset_index(0, drop=True)
df['return_cagr_fwd'] = df.groupby('entity_id')['return_cagr'].shift(-forecast_periods)
```

### Cross-sectional features

```python
# Percentile ranking within each time period
df['feature_rank'] = df.groupby('date')['feature'].rank(pct=True)

# Relative to benchmark (vs median)
median_by_date = df.groupby('date')['feature'].transform('median')
df['feature_vs_median'] = df['feature'] - median_by_date

# Sector-relative: rank within sector within time period
df['feature_sector_rank'] = df.groupby(['date', 'sector'])['feature'].rank(pct=True)
```

---

## SHAP value patterns

During training:

```python
import shap
explainer = shap.Explainer(model, df_X)
self.saveMeta({'shap-explainer': explainer})
```

For predictions:

```python
explainer = meta['shap-explainer']
shap_values = explainer(df_X)
df_shap = pd.DataFrame(shap_values.values, columns=df_X.columns, index=df_X.index)
```

Feature importance from SHAP:

```python
# Mean absolute SHAP = feature importance
mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
df_importance = pd.DataFrame({
    'feature': df_X.columns, 'importance': mean_abs_shap
}).sort_values('importance', ascending=False)
```

Prediction decomposition:

```python
# Top features driving predictions
top_features = df_shap.std().sort_values(ascending=False).index[:10].tolist()

# Breakdown: base + feature impacts = prediction
df_breakdown = df_shap[top_features].copy()
df_breakdown['base_value'] = explainer.expected_value
df_breakdown['other_features'] = df_shap.sum(1) - df_shap[top_features].sum(1)
df_breakdown['prediction'] = df_breakdown['base_value'] + df_shap.sum(1)
assert np.allclose(df_breakdown['prediction'], predictions)
```

---

## Logging in ML tasks

Two layers, different jobs (see SKILL.md "Log with `self.logger`"):

- **Lifecycle -> oryxflow.** `oryxflow.enable_logging()` (once, in `run.py`) prints
  task scheduling / completion / timing - the single most useful execution log.
  Do NOT reinvent it with your own start/end brackets around `flow.run()`.
- **Domain -> `self.logger`, inside `run()`.** Log the scalars you would watch
  live or grep: per-task shapes and date range, how much got dropped (`dropna` %),
  the model type / n_features / n_train_rows / a headline metric (rmse / f1), and
  the branch or fallback taken. One line per backtest ITERATION, never per row.

```python
self.logger.info("training cutoff {} -> predict {}", idate, idate_pred)
self.logger.warning("no data for {}", period)           # fallback / degenerate case
self.logger.warning("single-class fold at {} -> skipped", idate)
```

Use `self.logger`, NOT a raw `from loguru import logger`: `enable_logging()`
filters to the `oryxflow` namespace, so a raw loguru call from your task module is
silently dropped; `self.logger` emits inside that namespace and auto-tags
`task_id`.

**Log scalars + lifecycle; SAVE everything tabular or large** - frames, per-row
predictions, SHAP matrices, full metric tables, model objects, the comparison
xlsx go through `self.save()` (or an xlsx), never a log line. Rule of thumb:
scalars and lifecycle -> log; rows and artifacts -> `self.save()`.

**Plain (ANSI-free) output.** oryxflow's lifecycle logs are color-coded (ANSI
escape codes), noise in a saved log and on Windows. Because domain logs now share
the one oryxflow sink (via `self.logger`), a single switch governs both:
`oryxflow.enable_logging(colorize=False)`. (The default auto-detects - colored on a
terminal, plain when redirected to a file / pipe - so you often need nothing; pass
`colorize=False` to force plain.)

---

## Best practices

Use libraries, do not hand-roll (see SKILL.md "Use off-the-shelf libraries"):
- Regressions, statistical tests, time-series models (AR / ACF / ARIMA),
  cross-validation, metrics: use statsmodels / scipy.stats / sklearn. A numpy
  reimplementation is rarely more correct and is not DRY.
- A failed import is an ENV bug, not a cue to reimplement. ABI / version clashes
  (e.g. a scipy <-> statsmodels mismatch) often break only the umbrella import
  (`import statsmodels.api`) while the submodules (`statsmodels.regression`,
  `statsmodels.tsa`) still load - so probe, then STOP and offer to fix the env
  (pin / upgrade). Do not pivot to custom math to dodge the error.
- Legitimate reason to wrap a library call: a documented data quirk it mishandles
  (e.g. gap-aware lagging across missing periods). Even then, build ON the library
  where you can and VALIDATE the custom path against it (assert equal coefs on a
  clean slice) - do not replace it wholesale.

Data preparation:
- Merge validation: check no duplicates, minimal data loss.
- Sort before transformations: always sort by entity + time.
- Handle missing values: drop after transformations, validate <20% loss.
- No lookahead bias: never use future data in features (check shifts).

Feature engineering:
- Rates vs levels: use `diff()` for rates, `pct_change()` for levels.
- Clip outliers after `pct_change`.
- Cross-sectional ranks: `groupby('date').rank(pct=True)`.
- Time-series features: `groupby('entity_id').rolling()`.

Model training:
- Exclude missing targets before training.
- Set `random_state` for reproducibility.
- Save models in metadata, not the main output.
- Calculate the SHAP explainer during training; reuse for predictions.
- Add a `y_pred` column to the output.

Out-of-sample testing:
- Use an expanding window: train on [0:T], predict T+N.
- Avoid lookahead: never train on future data.
- Retrain each period for a realistic backtest.

SHAP values:
- Tree models only (LGBM, RF, XGBoost - not linear models).
- Calculate once during training, save in metadata.
- Reuse the explainer from metadata for predictions.
- Use mean absolute SHAP for feature-importance ranking.

---

## Quick reference

Common groupby operations:

```python
df.groupby('entity_id')['feature'].diff(4)           # YoY diff
df.groupby('entity_id')['feature'].pct_change(4)     # YoY % change
df.groupby('entity_id')['feature'].shift(-4)         # Forward shift
df.groupby('date')['feature'].rank(pct=True)         # Cross-sectional rank
df.groupby('entity_id')['feature'].rolling(4).mean() # Moving average
```

Load model and metadata:

```python
meta = self.metaLoad(key=0)  # From first dependency
model = meta['model']
explainer = meta['shap-explainer']
```

---

## Task organization checklist

When building an ML pipeline, create these tasks in order:

1. FeaturesRaw - merge data sources, create base features.
2. FeaturesTransform - transform features (normalize/rank), split X/y.
3. ModelTrain - train model, save in metadata, calculate SHAP.
4. ModelPerformanceIS - in-sample metrics, feature importance.
5. ModelPredictOS - out-of-sample backtest (expanding window).
6. ModelPredictCurrent - current-period predictions with SHAP.
7. RunAll - orchestration task (aggregates all steps). When the pipeline goes to
   prod, add a `RunAll...Prod` twin (frozen `params_prod`, selective resets, fresh
   data) - see "Productionizing: prod vs experiment" above.

Each task should: have a clear docstring; validate inputs/outputs with assertions;
return the appropriate output format (DataFrame, dict, pickle); use meaningful
names and consistent conventions.

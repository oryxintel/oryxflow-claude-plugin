# Claude Instructions: Building ML Pipelines with d6tflow

## ML Pipeline Architecture

Standard pipeline structure:
```
Data Loading → Feature Engineering → Model Training → Evaluation → Predictions
```

Typical task sequence:
```
FeaturesRaw → FeaturesTransform → ModelTrain → ModelPerformanceIS → ModelPredictOS → ModelPredictCurrent
```

---

## Core Principles

### 1. Data Structure Requirements

Define grouping columns in `cfg.py`:
```python
cfg.col_g_entity = ['sector', 'id']           # Entity identifiers
cfg.col_g_time = ['date']                      # Time column
cfg.col_g_entity_time = ['sector', 'id', 'date']  # Combined
```

### 2. Feature Organization

Organize features by type in `cfg.py`:
```python
cfg.col_X = ['feature1', 'feature2', ...]           # All features
cfg.col_X_rate = ['unemployment_rate', ...]         # Rate features (use diff not pct_change)
cfg.col_X_level = ['gdp', 'price', ...]            # Level features (use pct_change)
```

### 3. Multiple Output Pattern

Use `persist` for tasks with multiple outputs:
```python
class MyTask(d6tflow.tasks.TaskPqPandas):
    persist = ['all', 'x', 'y']  # or persists for dict outputs

    def run(self):
        self.save([df_all, df_X, df_y], from_list=True)
```

Load multiple outputs:
```python
df_all, df_X, df_y = self.inputLoad()
```

### 4. Metadata Pattern

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

## Pattern 1: Feature Engineering

### FeaturesRaw - Merge Data Sources

**Purpose**: Merge multiple data sources, create derived features

**Template**:
```python
@d6tflow.requires(DataSource1, DataSource2)
class FeaturesRaw(d6tflow.tasks.TaskPqPandas):
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

**Key concepts**:
- Merge on entity + time keys
- Validate: no duplicates, minimal data loss
- Use `how='left'` to preserve primary dataset

---

### FeaturesTransform - Transform for Modeling

**Purpose**: Transform features (normalize, rank, create time series features), split X/y

**Template**:
```python
@d6tflow.requires(FeaturesRaw)
class FeaturesTransform(d6tflow.tasks.TaskPqPandas):
    """Transform features for modeling"""
    transformx = d6tflow.Parameter()  # Transformation method
    transformy = d6tflow.Parameter()  # Target transformation
    persist = ['all', 'x', 'y']

    def run(self):
        df = self.input().load()
        df = df.sort_values(['entity_id', 'date'])  # Adjust to your columns

        # === Transform Features ===
        df_X = self.transform_features(df)

        # === Transform Target ===
        df_y = self.transform_target(df)

        # === Handle Missing Values ===
        df_X = df_X.dropna()
        assert df_X.shape[0] / df.shape[0] > 0.8, f"Dropped {100*(1-df_X.shape[0]/df.shape[0]):.1f}% of data"

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
            # Z-score normalization
            df_X = df[cfg.col_X].copy()
            df_X = (df_X - df_X.mean()) / df_X.std()
            return df_X

        elif self.transformx == 'rank':
            # Cross-sectional percentile ranking
            df_X = df[cfg.col_X].copy()
            for col in cfg.col_X:
                df_X[col] = df.groupby('date')[col].rank(pct=True)
            return df_X

        else:
            raise NotImplementedError(f"transformx={self.transformx}")

    def transform_target(self, df):
        """Apply target transformation based on transformy parameter"""
        if self.transformy == 'raw':
            return df['target']

        elif self.transformy == 'rank':
            # Cross-sectional percentile ranking
            return df.groupby('date')['target'].rank(pct=True)

        else:
            raise NotImplementedError(f"transformy={self.transformy}")
```

**Common transformations**:
- `raw`: Use features as-is
- `normalized`: Z-score normalization
- `rank`: Cross-sectional percentile ranking (0-1 scale)
- `log`: Log transformation for skewed data

**Critical steps**:
1. Sort by entity + time before transformations
2. Apply transformations separately to features and target
3. Drop NaN after transformations, validate <20% loss
4. Return `[df_all, df_X, df_y]`

---

## Pattern 2: Model Training

### ModelTrain - Train ML Model

**Purpose**: Train model, save model object in metadata, calculate SHAP values

**Template**:
```python
@d6tflow.requires(FeaturesTransform)
class ModelTrain(d6tflow.tasks.TaskPqPandas):
    """Train ML model and save predictions"""
    model = d6tflow.Parameter()  # Model type
    persist = ['all', 'x', 'y']

    def run(self):
        df_all, df_X, df_y = self.inputLoad()

        # Exclude rows with missing targets
        idxSel = df_all['target'].notna()
        df_all = df_all[idxSel]
        df_X = df_X[idxSel]
        df_y = df_y[idxSel]

        # Train model
        model = self.train_model(df_X, df_y)

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

**Critical steps**:
1. **Exclude missing targets** before training (recent periods may not have forward returns)
2. **Save model in metadata** (not main output)
3. **Calculate SHAP explainer** during training for tree models (reuse later)
4. **Add predictions** to DataFrame as `y_pred` column
5. **Always set random_state** for reproducibility

**For classification**:
```python
def train_model(self, X, y):
    import lightgbm

    # Handle imbalanced data
    if self.imbalanced:
        from imblearn.over_sampling import SMOTE
        X, y = SMOTE(random_state=42).fit_resample(X, y)

    return lightgbm.LGBMClassifier(
        class_weight='balanced',
        random_state=42
    ).fit(X, y)
```

---

## Pattern 3: Model Performance

### ModelPerformanceIS - In-Sample Metrics

**Purpose**: Calculate performance metrics and feature importance

**Template**:
```python
@d6tflow.requires(ModelTrain)
class ModelPerformanceIS(d6tflow.tasks.TaskPickle):
    """Calculate in-sample performance metrics"""

    def run(self):
        df_all, df_X, df_y = self.inputLoad()
        meta = self.metaLoad()
        model = meta['model']

        metrics = {}

        # === Calculate Metrics ===
        df_valid = df_all[['y', 'y_pred']].dropna()

        if self.is_regression():
            from sklearn.metrics import mean_squared_error, r2_score
            metrics['rmse'] = mean_squared_error(df_valid['y'], df_valid['y_pred'], squared=False)
            metrics['r2'] = r2_score(df_valid['y'], df_valid['y_pred'])
        else:
            from sklearn.metrics import accuracy_score, roc_auc_score
            metrics['accuracy'] = accuracy_score(df_valid['y'], df_valid['y_pred'])
            metrics['auc'] = roc_auc_score(df_valid['y'], df_valid['y_pred'])

        # === Feature Importance (tree models) ===
        if self.model in ['lgbm', 'rf', 'xgb']:
            import shap

            # SHAP-based importance
            shap_values = shap.Explainer(model)(df_X)
            mean_abs_shap = np.abs(shap_values.values).mean(axis=0)

            df_importance = pd.DataFrame({
                'feature': df_X.columns,
                'importance': mean_abs_shap
            }).sort_values('importance', ascending=False)

            metrics['feature_importance'] = df_importance
            metrics['shap_values'] = shap_values

        self.save(metrics)

    def is_regression(self):
        """Check if this is a regression task"""
        return self.model in ['lgbm', 'rf', 'ols'] and not hasattr(self, 'classification')
```

**Key metrics**:
- **Regression**: RMSE, R², MAE
- **Classification**: Accuracy, AUC, Precision/Recall
- **Feature Importance**: Mean absolute SHAP values (tree models)

---

## Pattern 4: Out-of-Sample Predictions

### ModelPredictOS - Expanding Window Backtest

**Purpose**: Generate out-of-sample predictions using expanding window to avoid lookahead bias

**Template**:
```python
@d6tflow.requires(ModelTrain, FeaturesTransform)
class ModelPredictOS(d6tflow.tasks.TaskPqPandas):
    """Generate out-of-sample predictions"""
    forecast_periods = d6tflow.IntParameter()  # Periods ahead to predict

    def run(self):
        # Load in-sample data and full dataset
        (df_trainIS, _, _), (df_full, df_X_full, df_y_full) = self.inputLoad()
        model = self.metaLoad(key=0)['model']

        # Get unique dates
        dates_train = sorted(df_trainIS['date'].unique())
        dates_all = sorted(df_full['date'].unique())

        # Start after minimum training period (e.g., 5 years)
        min_periods = 20  # Adjust based on your data frequency

        df_full['y_pred_os'] = np.nan

        # Expanding window loop
        for train_date in dates_train[min_periods:]:
            # Calculate prediction date (N periods forward)
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

**Critical concept**: **Expanding window** prevents lookahead bias
- Train on all data from start to time T
- Predict for time T + N (never use future data for training)
- Retrain model for each historical period

**Alternative: Rolling window** (not recommended - loses data):
```python
# Rolling window: train on [T-window:T], predict T+N
idx_train = (df['date'] > train_date - window) & (df['date'] <= train_date)
```

---

## Pattern 5: Current Period Predictions

### ModelPredictCurrent - Latest Predictions

**Purpose**: Generate predictions for the most recent period with SHAP values

**Template**:
```python
@d6tflow.requires(ModelTrain, FeaturesTransform)
class ModelPredictCurrent(d6tflow.tasks.TaskPqPandas):
    """Generate predictions for current period"""
    period_current = d6tflow.Parameter()  # e.g., '2025Q2', '2025-01-01'
    persist = ['predictions', 'features', 'shap']

    def run(self):
        # Get full dataset (includes current period)
        _, (df_all, df_X, _) = self.inputLoad()
        meta = self.metaLoad(key=0)
        model = meta['model']

        # Filter to current period
        idx_current = df_all['date'] == self.period_current
        if idx_current.sum() == 0:
            raise RuntimeError(f'No data for period {self.period_current}')

        df_current = df_all[idx_current].copy()
        df_X_current = df_X[idx_current].copy()

        # Generate predictions
        df_current['y_pred'] = model.predict(df_X_current)

        # Calculate SHAP values for interpretability
        df_shap = pd.DataFrame()
        if 'shap-explainer' in meta:
            shap_values = meta['shap-explainer'](df_X_current)
            df_shap = pd.DataFrame(
                shap_values.values,
                columns=df_X_current.columns,
                index=df_X_current.index
            )

        # Sort by prediction score
        df_current = df_current.sort_values('y_pred', ascending=False)

        self.save({
            'predictions': df_current,
            'features': df_X_current,
            'shap': df_shap
        })
```

**Key steps**:
1. Filter to specific prediction period
2. Use model trained on all historical data
3. Calculate SHAP values for top predictions (interpretability)
4. Sort by prediction score

---

## Common Feature Engineering Patterns

### Time-Based Features

**Year-over-Year Changes**:
```python
# For rates (use diff)
df['unemployment_rate_yoy'] = df.groupby('entity_id')['unemployment_rate'].diff(4)

# For levels (use pct_change)
df['gdp_yoy'] = df.groupby('entity_id')['gdp'].pct_change(4, fill_method=None)

# Clip extreme outliers
df['gdp_yoy'] = df['gdp_yoy'].clip(df['gdp_yoy'].quantile(0.01), df['gdp_yoy'].quantile(0.99))
```

**Moving Averages**:
```python
df['price_ma_4'] = df.groupby('entity_id')['price'].transform(lambda x: x.rolling(4).mean())
df['price_ma_12'] = df.groupby('entity_id')['price'].transform(lambda x: x.rolling(12).mean())
```

**Momentum Features**:
```python
df['momentum'] = df.groupby('entity_id')['price'].pct_change(4)
df['acceleration'] = df.groupby('entity_id')['momentum'].diff(1)
```

**Forward Targets** (for prediction):
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

### Cross-Sectional Features

**Percentile Ranking**:
```python
# Rank within each time period (cross-sectional)
df['feature_rank'] = df.groupby('date')['feature'].rank(pct=True)
```

**Relative to Benchmark**:
```python
# Entity feature vs median
median_by_date = df.groupby('date')['feature'].transform('median')
df['feature_vs_median'] = df['feature'] - median_by_date
```

**Sector-Relative**:
```python
# Rank within sector within time period
df['feature_sector_rank'] = df.groupby(['date', 'sector'])['feature'].rank(pct=True)
```

---

## SHAP Value Patterns

### During Training
```python
import shap
explainer = shap.Explainer(model, df_X)
self.saveMeta({'shap-explainer': explainer})
```

### For Predictions
```python
explainer = meta['shap-explainer']
shap_values = explainer(df_X)

# Convert to DataFrame
df_shap = pd.DataFrame(
    shap_values.values,
    columns=df_X.columns,
    index=df_X.index
)
```

### Feature Importance from SHAP
```python
# Mean absolute SHAP = feature importance
mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
df_importance = pd.DataFrame({
    'feature': df_X.columns,
    'importance': mean_abs_shap
}).sort_values('importance', ascending=False)
```

### Prediction Decomposition
```python
# Top features driving predictions
top_features = df_shap.std().sort_values(ascending=False).index[:10].tolist()

# Breakdown: base + feature impacts = prediction
df_breakdown = df_shap[top_features].copy()
df_breakdown['base_value'] = explainer.expected_value
df_breakdown['other_features'] = df_shap.sum(1) - df_shap[top_features].sum(1)
df_breakdown['prediction'] = df_breakdown['base_value'] + df_shap.sum(1)

# Validate
assert np.allclose(df_breakdown['prediction'], predictions)
```

---

## Best Practices

### Data Preparation
- **Merge validation**: Check no duplicates, minimal data loss
- **Sort before transformations**: Always sort by entity + time
- **Handle missing values**: Drop after transformations, validate <20% loss
- **No lookahead bias**: Never use future data in features (check shifts)

### Feature Engineering
- **Rates vs levels**: Use `diff()` for rates, `pct_change()` for levels
- **Clip outliers**: After pct_change, clip extreme values
- **Cross-sectional ranks**: Use `groupby(date).rank(pct=True)`
- **Time series features**: Use `groupby(entity_id).rolling()`

### Model Training
- **Exclude missing targets**: Filter before training (recent periods may lack forward returns)
- **Set random_state**: Always for reproducibility
- **Save in metadata**: Models go in metadata, not main output
- **SHAP explainer**: Calculate during training, reuse for predictions
- **Add predictions**: Include `y_pred` column in output DataFrame

### Out-of-Sample Testing
- **Use expanding window**: Train on [0:T], predict T+N
- **Avoid lookahead**: Never train on future data
- **Retrain each period**: For realistic backtest

### SHAP Values
- **Tree models only**: LGBM, RF, XGBoost (not linear models)
- **Calculate once**: During training, save in metadata
- **Reuse explainer**: From metadata for predictions
- **Mean absolute**: For feature importance ranking

---

## Quick Reference

**Common groupby operations**:
```python
df.groupby('entity_id')['feature'].diff(4)          # YoY diff
df.groupby('entity_id')['feature'].pct_change(4)    # YoY % change
df.groupby('entity_id')['feature'].shift(-4)        # Forward shift
df.groupby('date')['feature'].rank(pct=True)        # Cross-sectional rank
df.groupby('entity_id')['feature'].rolling(4).mean() # Moving average
```

**Load model and metadata**:
```python
meta = self.metaLoad(key=0)  # From first dependency
model = meta['model']
explainer = meta['shap-explainer']
```

**Multiple outputs**:
```python
# Save
self.save([df_all, df_X, df_y], from_list=True)

# Load
df_all, df_X, df_y = self.inputLoad()
```

**SHAP feature importance**:
```python
mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
```

---

## Task Organization Checklist

When building an ML pipeline, create these tasks in order:

1. **FeaturesRaw**: Merge data sources, create base features
2. **FeaturesTransform**: Transform features (normalize/rank), split X/y
3. **ModelTrain**: Train model, save in metadata, calculate SHAP
4. **ModelPerformanceIS**: In-sample metrics, feature importance
5. **ModelPredictOS**: Out-of-sample backtest (expanding window)
6. **ModelPredictCurrent**: Current period predictions with SHAP
7. **RunAll**: Orchestration task (aggregates all steps)

Each task should:
- Have clear docstring describing purpose
- Validate inputs/outputs with assertions
- Return appropriate output format (DataFrame, dict, pickle)
- Use meaningful variable names
- Follow consistent naming conventions

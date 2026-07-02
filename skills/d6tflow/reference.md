# d6tflow Reference: Working with d6tflow Workflows

Comprehensive LIBRARY reference loaded on demand by the `d6tflow` skill. Covers
core concepts in depth, task types, working with tasks, running workflows,
advanced patterns, best practices, avoiding silent data errors, data-science
recipes, and debugging. For the HOUSE conventions - project layout, grouping
supporting code, and naming columns / tasks / variables - see
[conventions.md](conventions.md).

## What is d6tflow?

**d6tflow** is a Python library for building highly effective data science
workflows. It lets you chain together complex, parameterized data flows and
execute them, caching intermediate calculations so you build better models
faster.

### Key Benefits
- **Dependency management**: Automatically runs tasks in the correct order
- **Caching**: Only re-runs tasks when inputs change
- **Parameter tracking**: Different parameters create different task instances
- **Data persistence**: Automatically saves/loads data between tasks
- **Reproducibility**: Complete lineage of data transformations

### When to Use d6tflow
- Multi-step data pipelines (loading -> cleaning -> features -> models -> predictions)
- Machine learning workflows with dependencies between tasks
- Workflows that need to be re-run with different parameters
- Projects where you want automatic caching and incremental computation

---

## Core Concepts

### 1. Tasks

Building blocks: Inherit from d6tflow task class, have `run()` method, save
outputs automatically, uniquely identified by class name + parameters.

**Naming**: name a task for the OUTPUT it produces (a noun: `OEWSWages`,
`CleanedSales`, `TrainedModel`, `DataOEWS`), not the verb it performs; avoid
generic names like `GetData` / `LoadData` / `Process`; order tokens broad ->
narrow so a family clusters (`FundamentalsLeadLag`, not `LeadLagAnalysis`). Full
rules in [conventions.md](conventions.md) ("Task naming"). Some examples below use
older verb-style names for brevity; prefer output names in real code.

```python
import d6tflow
import pandas as pd

class LoadData(d6tflow.tasks.TaskPqPandas):
    """Load raw data from CSV"""
    def run(self):
        df = pd.read_csv('data.csv')
        self.save(df)  # Auto-saves as parquet
```

### 2. Task Types

| Task Type | Output Format | Use Case |
|-----------|---------------|----------|
| `TaskPqPandas` | Parquet | DataFrames (default choice, fast) |
| `TaskCSVPandas` | CSV | DataFrames (human-readable) |
| `TaskExcelPandas` | Excel | DataFrames (for reports) |
| `TaskPickle` | Pickle | Any Python object (models, dicts, lists) |
| `TaskJson` | JSON | Dictionaries, simple data structures |
| `TaskAggregator` | None | Runs dependencies without saving output |

**Best Practice**: Use `TaskPqPandas` for DataFrames (fastest), `TaskPickle`
for models/objects.

### 3. Dependencies

Declare with `@d6tflow.requires()` decorator. Auto-runs tasks in correct order.

```python
@d6tflow.requires(LoadData)
class CleanData(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()  # Load from LoadData
        self.save(df.dropna())

# Multiple dependencies
@d6tflow.requires(LoadData, LoadMetadata)
class MergeData(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df_data, df_meta = self.inputLoad()
        self.save(df_data.merge(df_meta, on='id'))
```

### 4. Parameters

Parameters make tasks dynamic and reusable. They affect task identity:

```python
class ProcessData(d6tflow.tasks.TaskPqPandas):
    date = d6tflow.DateParameter()
    region = d6tflow.Parameter()
    threshold = d6tflow.IntParameter(default=100)

    def run(self):
        df = self.input().load()
        df = df[df['region'] == self.region]
        df = df[df['value'] > self.threshold]
        self.save(df)
```

**Parameter Types**:
- `d6tflow.Parameter()` - String
- `d6tflow.IntParameter()` - Integer
- `d6tflow.FloatParameter()` - Float
- `d6tflow.BoolParameter()` - Boolean
- `d6tflow.DateParameter()` - Date
- `d6tflow.ListParameter()` - List
- `d6tflow.DictParameter()` - Dictionary
- `d6tflow.ChoiceParameter(choices=['rf','lgbm'], default='rf')` - string
  restricted to a fixed set; an off-list value raises at task construction
  (fail-fast on typos), NOT deep in downstream code. Values stay plain strings,
  so it drops into existing string-valued params with zero churn - prefer this
  for categoricals like `model='rf'`.
- `d6tflow.EnumParameter(enum=MyEnum)` - value is an `enum.Enum` member (pass the
  enum class). Same fail-fast benefit but heavier: you define an `enum.Enum` and
  rewrite values from `'rf'` to `MyEnum.rf`. Use only when you genuinely want
  enum objects; for plain string choices, `ChoiceParameter` is lighter.

**Important**: Same class + same parameters = same task instance (cached).
Different parameters = different task instance (separate cache).

### 5. Parameter Inheritance

Parameters auto-inherit from dependencies. Use `significant=False` for params
that do not affect task identity:

```python
class TaskA(d6tflow.tasks.TaskPqPandas):
    date = d6tflow.DateParameter()
    verbose = d6tflow.BoolParameter(default=False, significant=False)

@d6tflow.requires(TaskA)
class TaskB(d6tflow.tasks.TaskPqPandas):
    # Auto-inherits 'date' and 'verbose' from TaskA
    def run(self):
        df = self.inputLoad()
        # self.date available here
```

---

## Working with Tasks

### Load / save cheat-sheet

Pick the identifier by WHAT (data vs meta), WHERE (inside `run()` vs outside with
a `flow`), and HOW MANY (all vs one):

| What you want                | Inside `run()`                          | Outside (have `flow`)              |
|------------------------------|-----------------------------------------|------------------------------------|
| Declare N outputs            | `persists = ['a','b']` (class attr)     | -                                  |
| Save N outputs, list form    | `self.save([a, b], from_list=True)`     | -                                  |
| Save N outputs, dict form    | `self.save({'a': a, 'b': b})`           | -                                  |
| Save metadata                | `self.saveMeta({'model': m})`           | -                                  |
| Load ALL outputs             | `self.inputLoad()` -> tuple             | `flow.outputLoad(Task)`            |
| Load ONE output (by name)    | `self.inputLoad(keys='a')`              | `flow.outputLoad(Task, keys='a')`  |
| Pick ONE dependency          | `self.inputLoad(task='name')`           | -                                  |
| Load metadata                | `self.metaLoad(key=0)`                   | `flow.outputLoadMeta(Task)`        |

Notes:
- An OUTPUT is selected by name (`keys=`); a DEPENDENCY by name/index (`task=`,
  or `self.input()[i]` for positional `requires`). `[0]`/`[1]` NEVER picks an
  output.
- Lower-level "load one output": `self.input()['a'].load()` - index the persist
  NAME first, THEN `.load()`. `self.input().load(keys='a')` does NOT work for a
  multi-`persists` dep (`self.input()` is a dict, not a target).
- TRAP: `load()`/`inputLoad()` swallow unknown kwargs silently, so a wrong
  selector returns the whole/default output with NO error - e.g.
  `load(persist='a')` (the kwarg is `keys=`, not `persist=`).

### Loading Data from Upstream Tasks

Rule: prefer `self.inputLoad()` - it returns the DATA. `self.input()` returns the
raw Target (use it only for `.path` or a deliberate `.load()`). Select an output
with `keys=` (never `persist=` - that kwarg is silently ignored; see trap above).

```python
# Single dependency, single output
@d6tflow.requires(UpstreamTask)
class MyTask(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()

# Single dependency, multiple outputs (persists=['train','test'])
@d6tflow.requires(SplitData)
class MyTask(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df_train, df_test = self.inputLoad()        # all outputs, in persists order
        df_train = self.inputLoad(keys='train')     # just one, by name
        df_train = self.input()['train'].load()     # lower-level equivalent

# Multiple dependencies - PREFER the named-dict form (select deps by name)
@d6tflow.requires({'data': LoadData, 'meta': LoadMetadata})
class MyTask(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df_data = self.inputLoad(task='data')       # or self.input()['data'].load()
        df_meta = self.inputLoad(task='meta')

# Multiple dependencies, positional - select deps by INTEGER index
@d6tflow.requires(Task1, Task2, Task3)
class MyTask(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df1, df2, df3 = self.inputLoad()
```

Selection rules - `self.input()` mirrors `requires()`:

- single dep, single output -> a Target -> `self.input().load()`
- single dep, multiple `persists` -> a `{name: target}` dict ->
  `self.input()['train'].load()`
- positional `requires(T0, T1)` -> a list -> `self.input()[0]` (and
  `self.input()[0]['train']` if T0 has multiple outputs)
- named `requires({'a': T0, 'b': T1})` -> a dict -> `self.input()['a']`

(For the by-name vs by-index rule and the silent-unknown-kwarg trap, see the
cheat-sheet above.)

### Saving Multiple Outputs

```python
class SplitData(d6tflow.tasks.TaskPqPandas):
    persists = ['train', 'test', 'valid']  # output names
    def run(self):
        df = self.inputLoad()
        # list -> saved positionally, in persists order; needs from_list=True
        self.save([df.sample(frac=0.7), df.sample(frac=0.2), df.sample(frac=0.1)], from_list=True)

# Loading
@d6tflow.requires(SplitData)
class TrainModel(d6tflow.tasks.TaskPickle):
    def run(self):
        df_train, df_test, df_valid = self.inputLoad()

# Dictionary outputs - same persists; dict keys select by name
class MyTask(d6tflow.tasks.TaskPqPandas):
    persists = ['data', 'metadata']
    def run(self):
        self.save({'data': df_main, 'metadata': df_meta})
```

`persists` names the outputs; `persist` (singular) is a backwards-compatible
alias for the same attribute. List-vs-dict is chosen by what you pass to
`save()`, not by the attribute name.

### Saving Metadata (Models, Configs)

For models and configs that do not fit standard formats:

```python
class TrainModel(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()
        model = RandomForestClassifier()
        model.fit(df[features], df['target'])
        df['pred'] = model.predict(df[features])
        self.save(df)
        self.saveMeta({'model': model, 'accuracy': 0.95, 'features': features})

# Loading metadata
@d6tflow.requires(TrainModel)
class ApplyModel(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()
        meta = self.metaLoad()
        df['pred'] = meta['model'].predict(df[meta['features']])
        self.save(df)

# Load from specific dependency (key=0 is first)
@d6tflow.requires(TrainModel, LoadData)
class MyTask(d6tflow.tasks.TaskPqPandas):
    def run(self):
        meta = self.metaLoad(key=0)  # From TrainModel
        df = self.input()[1].load()  # From LoadData
```

---

## Running Workflows

### Basic Execution

```python
# flow.py - Create workflow
flow = d6tflow.Workflow(FinalTask, params={'date': '2024-01-01'})

# run.py - Execute
result = flow.run()
print(result.summary())          # ran / cache-hit / failed; result.success/.ran/.failed to drill down
df = flow.outputLoad()

# Check status
flow.preview()   # Preview what will run
flow.complete()  # Returns True if all tasks complete
```

### Forcing Re-runs & Loading Outputs

```python
# Reset (force re-run) - flow.reset is the preferred path
flow.reset(TaskName)                      # specific task + downstream (no prompt by default)
flow.reset(TaskName, confirm=True)        # opt IN to a confirmation prompt
flow.resetAll()                           # entire workflow
flow.run([TaskName()], forced_all=True)   # force this task + its upstream
flow.run(forced_all_upstream=True)        # force everything

# Load outputs
result = flow.outputLoad()                # Final task
df = flow.outputLoad(IntermediateTask)    # Specific task
df_train = flow.outputLoad(SplitData, keys='train')  # Specific output by name
meta = flow.metaLoad(TrainModel)          # Metadata
```

**When to reset**: Source data changed, task code changed, or you want fresh
results. `flow.reset(TaskName)` cascades to downstream tasks, so resetting the
one task you changed is enough.

**Code edits vs parameter changes (the iterate gotcha)**: d6tflow caches by task
identity = class + parameters. A PARAMETER change creates a new identity, so it
is auto-detected and reruns on the next `flow.run()` with no reset. A CODE edit
(changing a task's `run()` body) does NOT change identity - d6tflow still treats
the task as complete and SKIPS it, reusing the stale output. So after editing a
task's code you MUST `flow.reset(thatTask)` before running, or the edit silently
has no effect. This is the most common d6tflow surprise when iterating.
`flow.reset` already cascades downstream, so it IS the whole workflow - never write
a reset helper (`reset_if_code_changed`, a downstream-resetter); reaching for one
means the built-in was missed. (If a PARAMETER change is not auto-rerunning, the
fix is to define / inherit the parameter correctly, not to reset by hand.)

**Changing a task's output columns** is just such a code edit: adding, removing,
or renaming a column needs a reset (cascades downstream) and a matching update to
the docstring's output contract. Removing or renaming a column breaks downstream
tasks that read it - the cascade re-runs them, so the break surfaces as an error
you fix in the same change. Subtler: changing what an EXISTING column MEANS
(recomputed values, new units) WITHOUT renaming it does not error downstream -
dependents silently consume the new semantics, so reset and re-verify them.

### Important: Trust Auto File Management

d6tflow auto-handles file creation. DO NOT manually verify files after running
tasks.

- Don't: `flow.run()` then `ls data/TaskName/` or check paths
- Do: `flow.run()` then `df = flow.outputLoad(TaskName)`

If `flow.run()` completes without errors, files exist. Debug by loading data
with `flow.outputLoad()`, not by checking the file system.

---

## Advanced Patterns

### Pattern 1: Compare a named set of parameter variants (WorkflowMulti)

Use ONE `WorkflowMulti` keyed by name to run/compare a fixed set of param sets
(models, dates, cohorts) - one importable object, named access, no ad-hoc loop:

```python
# params is a dict KEYED BY FLOW NAME; each value is a param set
wf = d6tflow.WorkflowMulti(FinalTask, {
    'lgbm':    {'model': 'lgbm'},
    'xgboost': {'model': 'xgboost'},
    'rf':      {'model': 'rf'},
})
res = wf.run()                             # all flows; wf.run(flow='lgbm') for one
print(res.summary())                       # per-flow summary blocks; res['lgbm'] -> that flow's RunResult
wf.reset(tasks.Train, flow='rf')           # per-flow reset

df   = wf.outputLoad(tasks.Predict, flow='xgboost')  # one flow -> its output
alldf = wf.outputLoad(tasks.Predict)                 # omit flow= -> {name: output}
```

Notes:
- A **list** of param sets also works, but the keys become integer indices
  (`0, 1, 2`) - prefer the named dict so `flow=` and loaded results are labelled.
- If a dict *value* is a list, WorkflowMulti expands the cross-product of those
  values into separate flows (a param sweep).
- `wf.run()` returns a `{name: RunResult}` (a `MultiRunResult`) that also carries
  `.summary()`/`.success`, so `print(res.summary())` reads the same as a single
  flow; index `res['lgbm']` for one flow's `RunResult` to drill in (`.ran`/`.failed`).
- `d6tflow.runLoad(task, params=..., reset=False)` is the module-level
  run-and-load-in-one-call helper for a single param set (see below).

See the escalation note in SKILL.md for the full signatures - confirm against the
installed package (`inspect.signature(d6tflow.WorkflowMulti.outputLoad)`) rather
than assuming.

### Pattern 1b: Dynamic Task Creation

```python
import d6tflow.utils

params_base = {'threshold': 100}
params_list = d6tflow.utils.params_generator_dictlist(
    {'date': ['2024-01-01', '2024-01-02', '2024-01-03']},
    params_base
)
# Result: one dict per date, each with threshold=100

flow = d6tflow.WorkflowMulti(FinalTask, params_list)
flow.run()
```

### Pattern 2: Workflow Orchestration Task

Create a task that just runs dependencies without saving output:

```python
@d6tflow.requires(Task1, Task2, Task3)
class RunAll(d6tflow.tasks.TaskJson):
    def run(self):
        self.save({'status': 'complete', 'timestamp': datetime.now()})
```

### Pattern 3: Nested Workflows

```python
class MasterTask(d6tflow.tasks.TaskPqPandas):
    def run(self):
        results = []
        for region in ['US', 'EU', 'ASIA']:
            sub_flow = d6tflow.Workflow(ProcessRegion, params={'region': region})
            sub_flow.run()
            results.append(sub_flow.outputLoad())
        self.save(pd.concat(results))
```

### Pattern 4: Incremental Processing

```python
class IncrementalTask(d6tflow.tasks.TaskPqPandas):
    date = d6tflow.DateParameter()

    def run(self):
        prev_date = self.date - timedelta(days=1)
        try:
            prev_task = IncrementalTask(date=prev_date)
            df_prev = prev_task.output().load() if prev_task.complete() else pd.DataFrame()
        except Exception:
            df_prev = pd.DataFrame()

        df_new = pd.read_csv(f'data_{self.date}.csv')
        self.save(pd.concat([df_prev, df_new]))
```

---

## Configuration

### Environment-Based Configuration

```python
class MyTask(d6tflow.tasks.TaskPqPandas):
    env = d6tflow.Parameter(significant=False)  # 'dev' or 'prod'

    def run(self):
        if self.env == 'dev':
            df = pd.read_csv('sample.csv')
        else:
            df = pd.read_csv('full.csv')
        self.save(df)

flow = d6tflow.Workflow(MyTask, params={'env': 'dev'})
```

### Custom Task Directories

```python
class MyTask(d6tflow.tasks.TaskPqPandas):
    def output(self):
        return d6tflow.targets.PqPandas(path='/custom/path/output.parquet')
```

---

## Best Practices

### 1. Task Design

Do:
- Keep tasks focused on a single responsibility
- Name tasks for their OUTPUT (a noun: `OEWSWages`, `CleanedSales`,
  `TrainedModel`), not the verb they perform (see "Tasks > Naming")
- Write the docstring as real documentation: purpose + input/output contract +
  quirks. It explains intent; do NOT restate the run() code (a short snippet
  only when it is the clearest way to state a contract)
- Use type hints for clarity
- Validate inputs and outputs with assertions

Don't:
- Create monolithic tasks that do everything
- Use generic names like `GetData`, `Process`, `Task1`
- Paste the code into the docstring, or settle for a one-line "brief description"
- Skip error handling
- Assume data shape/columns without validation

```python
class CalculateFeatures(d6tflow.tasks.TaskPqPandas):
    """
    Calculate rolling averages and momentum features

    Input: DataFrame with columns ['date', 'value']
    Output: DataFrame with additional columns ['ma_30', 'ma_90', 'momentum']
    """
    def run(self):
        df = self.input().load()

        assert 'date' in df.columns, "Missing 'date' column"
        assert 'value' in df.columns, "Missing 'value' column"
        assert df.shape[0] > 0, "Empty DataFrame"

        df['ma_30'] = df['value'].rolling(30).mean()
        df['ma_90'] = df['value'].rolling(90).mean()
        df['momentum'] = df['value'].pct_change(30)

        assert not df['ma_30'].isna().all(), "All ma_30 values are NaN"
        self.save(df)
```

### 2. Parameter Management

Do:
- Define parameters at the top of the class
- Use appropriate parameter types
- Provide sensible defaults
- Use `significant=False` for non-data-affecting parameters
- Keep parameters in a separate config file/dict

Don't:
- Hard-code values that should be parameters
- Use parameters for values that never change
- Create too many parameters (makes task identity complex)

```python
# Good - centralized parameters
params = {
    'date': '2024-01-01', 'region': 'US', 'model_type': 'rf',
    'n_estimators': 100, 'test_size': 0.2
}
flow = d6tflow.Workflow(FinalTask, params=params)
```

### 3. Data Validation

Do:
- Assert expected columns exist
- Check for null values where unexpected
- Validate data shapes
- Check value ranges
- Log warnings for anomalies

```python
class ValidatedTask(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df = self.input().load()

        required_cols = ['id', 'date', 'value']
        assert all(c in df.columns for c in required_cols), \
            f"Missing columns. Have: {df.columns.tolist()}, Need: {required_cols}"
        assert df['id'].isna().sum() == 0, "Null IDs found"
        assert df.shape[0] > 0, "Empty DataFrame"
        assert df.shape[1] >= 3, "Too few columns"
        assert df['value'].min() >= 0, "Negative values found"
        assert not df.duplicated('id').any(), "Duplicate IDs found"

        self.save(df)
```

### 4. Error Handling & Documentation

Use `self.logger` for in-task domain logging (and `d6tflow.enable_logging()` for
task lifecycle - see ml-patterns.md "Logging in ML tasks"); let the pipeline fail
natively (avoid try-except); give
every task a real docstring (purpose + input/output contract + quirks - see
"Task Design" above, and the SKILL "Task docstrings" rule).

---

## Avoiding silent data errors

The traps that produce a WRONG NUMBER with no exception - the dangerous kind,
because nothing fails. These bite the AI agent especially: an assumed column
meaning or an unvalidated join yields a confident, wrong analysis. Guard against
them explicitly.

### Validate every merge/join

A bad join key silently multiplies or drops rows and every number downstream is
wrong, with no error. Make the assumption explicit and let pandas enforce it:

```python
df = df_left.merge(df_right, on='id', how='left', validate='m:1')  # raises if right side isn't unique
assert len(df) == len(df_left), f"left join changed row count {len(df_left)} -> {len(df)}"
```

- Pass `validate=` (`'1:1'`, `'m:1'`, `'1:m'`) on EVERY merge - it raises if the
  key cardinality is not what you assumed (the usual cause of row blow-up).
- Check the row count before/after. A left join that grows the frame means the
  right key was not unique; an inner join that shrinks it means keys did not match
  (often a dtype or whitespace mismatch in the key - `'01'` vs `1`).
- After the merge, check `df[key].isna().sum()` on columns that should be fully
  populated - NaNs there flag unmatched rows.

### Verify before you conclude

Before stating ANY finding from a frame, look at it - do not assume its shape or
a column's meaning:

```python
print(df.shape, df.dtypes.to_dict())
print(df.isna().sum())
print(df.describe())            # ranges sane? a "rate" in [0,1] vs [0,100]?
```

Reconcile aggregates against a known total (sum of parts == whole; a group count
sums to the row count). A subtotal that does not reconcile means a filter, a
dropped NaN, or a double-counted join - find it before reporting the number.

### Quote computed numbers, never eyeball them

Every figure in prose or a report comes from the FRAME, pulled and rounded
explicitly - never read off a chart, guessed, or carried from memory:

```python
val = df.loc[df['sector'] == 'Tech', 'yield_dividend'].iloc[0]
print(f"Tech dividend yield: {val:.1%}")   # quote THIS, not "looks like ~6%"
```

A chart is for shape and direction; the number behind it comes from the data. If
a claim needs a value, compute it.

### Watch pandas index alignment

Arithmetic between two Series aligns on the INDEX, not on position. If two frames
have mismatched indices (one was filtered or sorted), `a['x'] - b['y']` pairs by
label and yields NaNs or silently wrong values - it does not error.

```python
# WRONG if df_a, df_b have different indices after a filter/sort
df_a['delta'] = df_a['value'] - df_b['value']
# Safer: align deliberately, or operate on .values for positional, or reset_index
df_a['delta'] = df_a['value'].values - df_b['value'].values   # positional, intentional
```

When combining columns from separately-built frames, `reset_index(drop=True)`
first, or merge on a key, rather than trusting positional alignment.

---

## Common Patterns for Data Science

### Train/Test Split

```python
class SplitData(d6tflow.tasks.TaskPqPandas):
    persists = ['train', 'test']
    test_size = d6tflow.FloatParameter(default=0.2)
    def run(self):
        from sklearn.model_selection import train_test_split
        df_train, df_test = train_test_split(self.inputLoad(), test_size=self.test_size, random_state=42)
        self.save([df_train, df_test], from_list=True)
```

### Feature Engineering

```python
@d6tflow.requires(CleanData)
class EngineerFeatures(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()
        df['hour'] = df['timestamp'].dt.hour
        df['value_lag1'] = df.groupby('id')['value'].shift(1)
        df['value_ma7'] = df.groupby('id')['value'].rolling(7).mean().reset_index(0, drop=True)
        self.save(df)
```

### Model Training & Evaluation

```python
@d6tflow.requires({'split': SplitData, 'features': EngineerFeatures})
class TrainModel(d6tflow.tasks.TaskPqPandas):
    persists = ['predictions', 'metrics']
    def run(self):
        df_train = self.input()['split']['train'].load()  # dep by name, output by name
        feature_cols = [c for c in self.inputLoad(task='features').columns if c.startswith('feature_')]
        model = RandomForestRegressor(n_estimators=100).fit(df_train[feature_cols], df_train['target'])
        df_test = self.input()['split']['test'].load()
        df_test['pred'] = model.predict(df_test[feature_cols])
        metrics = {'rmse': mean_squared_error(df_test['target'], df_test['pred'], squared=False)}
        self.save([df_test, pd.DataFrame([metrics])], from_list=True)
        self.saveMeta({'model': model, 'features': feature_cols})
```

---

## Debugging d6tflow Workflows

- **Task not running**: Already complete (cached) -> `flow.reset(TaskName); flow.run()`
- **Parameters not affecting task**: Check `significant=False` or parameter type
- **Cannot load multiple outputs**: Mismatch between `persists` list and `save()` count
- **Metadata not loading**: Not saved, or loading from wrong task (use `metaLoad(key=0)` for first dependency)

---

## Quick Reference

```python
# Create task
class MyTask(d6tflow.tasks.TaskPqPandas):
    param = d6tflow.Parameter()
    def run(self):
        self.save(result)

# Add dependencies
@d6tflow.requires(UpstreamTask)
class MyTask(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()

# Run workflow
flow = d6tflow.Workflow(FinalTask, params={'param': 'value'})
flow.run()
result = flow.outputLoad()

# Force re-run
flow.reset(TaskName); flow.run()

# Multiple outputs
class MyTask(d6tflow.tasks.TaskPqPandas):
    persists = ['a', 'b']
    def run(self):
        self.save([df_a, df_b], from_list=True)

# Metadata
self.saveMeta({'model': model})
meta = self.metaLoad(); model = meta['model']
```

---

## Project layout, code organization, and naming -> conventions.md

The project-structure deep dive (every file's role and how they wire together),
the subject-grouping rules for `eda/` / `utils/` / `viz/`, and the naming
conventions (columns, tasks, DataFrames) live in
[conventions.md](conventions.md) - the house-style companion to this library
reference. Load it when you organize files or name things.

## Additional Resources

- Official docs: https://d6tflow.readthedocs.io/
- GitHub: https://github.com/d6t/d6tflow

---

## Summary

d6tflow: Reproducible, cacheable data science workflows. Tasks (classes with
`run()`), dependencies (`@d6tflow.requires()`), parameters (task variants),
auto-caching, multiple outputs (`persists`), metadata (models/configs).

**Use for**: Multi-step pipelines, ML workflows, reproducible research.
**Avoid for**: Simple scripts, real-time systems, single-step processes.

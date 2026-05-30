# d6tflow Reference: Working with d6tflow Workflows

Comprehensive reference loaded on demand by the `d6tflow` skill. Covers core
concepts in depth, task types, working with tasks, running workflows, advanced
patterns, best practices, data-science recipes, debugging, and the full project
structure walkthrough.

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

### Loading Data from Upstream Tasks

```python
# Single input
@d6tflow.requires(UpstreamTask)
class MyTask(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()

# Multiple inputs
@d6tflow.requires(Task1, Task2, Task3)
class MyTask(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df1, df2, df3 = self.inputLoad()

# Named inputs
@d6tflow.requires({'data': LoadData, 'meta': LoadMetadata})
class MyTask(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df_data = self.input()['data'].load()
        df_meta = self.input()['meta'].load()
```

### Saving Multiple Outputs

```python
class SplitData(d6tflow.tasks.TaskPqPandas):
    persist = ['train', 'test', 'valid']  # Names for outputs
    def run(self):
        df = self.inputLoad()
        self.save([df.sample(frac=0.7), df.sample(frac=0.2), df.sample(frac=0.1)], from_list=True)

# Loading
@d6tflow.requires(SplitData)
class TrainModel(d6tflow.tasks.TaskPickle):
    def run(self):
        df_train, df_test, df_valid = self.inputLoad()

# Dictionary outputs
class MyTask(d6tflow.tasks.TaskPqPandas):
    persists = ['data', 'metadata']  # Note: 'persists' with 's'
    def run(self):
        self.save({'data': df_main, 'metadata': df_meta})
```

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
flow.run()
result = flow.outputLoad()

# Check status
flow.preview()   # Preview what will run
flow.complete()  # Returns True if all tasks complete
```

### Forcing Re-runs & Loading Outputs

```python
# Reset (force re-run)
flow.reset(TaskName)                      # Reset specific task + downstream
flow.reset(TaskName, confirm=False)       # No confirmation
flow.resetAll()                           # Reset entire workflow

# Load outputs
result = flow.outputLoad()                # Final task
df = flow.outputLoad(IntermediateTask)    # Specific task
df_train = flow.outputLoad(SplitData, keys='train')  # Specific persist
meta = flow.metaLoad(TrainModel)          # Metadata
```

**When to reset**: Source data changed, task code changed, parameters changed
(usually auto-detected), want fresh results.

### Important: Trust Auto File Management

d6tflow auto-handles file creation. DO NOT manually verify files after running
tasks.

- Don't: `flow.run()` then `ls data/TaskName/` or check paths
- Do: `flow.run()` then `df = flow.outputLoad(TaskName)`

If `flow.run()` completes without errors, files exist. Debug by loading data
with `flow.outputLoad()`, not by checking the file system.

---

## Advanced Patterns

### Pattern 1: Dynamic Task Creation

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
- Use descriptive task names (verbs: Load, Clean, Transform, Train, Predict)
- Add docstrings explaining what the task does
- Use type hints for clarity
- Validate inputs and outputs with assertions

Don't:
- Create monolithic tasks that do everything
- Use generic names like `Task1`, `Task2`
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

Use loguru for logging. Let the pipeline fail natively (avoid try-except). Add
docstrings to every task.

```python
class CalculateReturns(d6tflow.tasks.TaskPqPandas):
    """
    Calculate forward returns for each asset
    Input: DataFrame ['date', 'asset_id', 'price'], sorted by ['asset_id', 'date']
    Output: + columns ['return_1d', 'return_5d', 'return_20d']
    """
    horizon_days = d6tflow.ListParameter(default=[1, 5, 20])
    def run(self):
        pass  # implementation
```

---

## Common Patterns for Data Science

### Train/Test Split

```python
class SplitData(d6tflow.tasks.TaskPqPandas):
    persist = ['train', 'test']
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
@d6tflow.requires(SplitData, EngineerFeatures)
class TrainModel(d6tflow.tasks.TaskPqPandas):
    persist = ['predictions', 'metrics']
    def run(self):
        df_train = self.input()[0].load(persist='train')
        feature_cols = [c for c in self.inputLoad()[1].columns if c.startswith('feature_')]
        model = RandomForestRegressor(n_estimators=100).fit(df_train[feature_cols], df_train['target'])
        df_test = self.input()[0].load(persist='test')
        df_test['pred'] = model.predict(df_test[feature_cols])
        metrics = {'rmse': mean_squared_error(df_test['target'], df_test['pred'], squared=False)}
        self.save([df_test, pd.DataFrame([metrics])], from_list=True)
        self.saveMeta({'model': model, 'features': feature_cols})
```

---

## Debugging d6tflow Workflows

- **Task not running**: Already complete (cached) -> `flow.reset(TaskName); flow.run()`
- **Parameters not affecting task**: Check `significant=False` or parameter type
- **Cannot load multiple outputs**: Mismatch between `persist` list and `save()` count
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
    persist = ['a', 'b']
    def run(self):
        self.save([df_a, df_b], from_list=True)

# Metadata
self.saveMeta({'model': model})
meta = self.metaLoad(); model = meta['model']
```

---

## Project Structure (deep dive)

d6tflow projects follow a standard file organization that separates concerns.

### Typical File Layout

```
project/
|-- tasks.py           # Workflow task definitions
|-- cfg.py             # Global configuration and settings
|-- flow_params.py     # Workflow-specific parameters
|-- flow.py            # Workflow instance definition
|-- run.py             # Execute workflow tasks
|-- visualize.py       # Use outputs for analysis (script)
|-- visualize.ipynb    # Use outputs for analysis (notebook)
`-- .creds.yaml        # Protected credentials (NOT committed to git)
```

### Separation of Concerns

1. **Configuration Layer** (`cfg.py` + `flow_params.py`)
   - `cfg.py`: Global settings (environment, dates, credentials)
   - `flow_params.py`: Workflow-specific task parameters
2. **Definition Layer** (`tasks.py` + `flow.py`)
   - `tasks.py`: Define what each task does
   - `flow.py`: Define which tasks to run with which parameters
3. **Execution Layer** (`run.py`): Execute the workflow
4. **Analysis Layer** (`visualize.py` + `visualize.ipynb`): Load and analyze outputs

**Key advantage**: Define your workflow once in `flow.py`, then import it
everywhere (`from flow import flow`). Consistency across execution, analysis,
and notebooks.

### File Descriptions

#### `tasks.py` - Workflow Tasks

```python
import d6tflow
import pandas as pd
import cfg

class GetData(d6tflow.tasks.TaskPqPandas):
    """Load raw data"""
    def run(self):
        df = pd.DataFrame({'a': range(10)})
        self.save(df)

@d6tflow.requires(GetData)
class Process(d6tflow.tasks.TaskPqPandas):
    """Process the raw data"""
    optional = d6tflow.BoolParameter(default=False)

    def run(self):
        df = self.input().load()
        if self.optional:
            df = df * 2
        self.save(df)
```

Best practices: one file for simple projects; can split into multiple files for
complex projects (e.g. `tasks_etl.py`, `tasks_models.py`). Keep tasks focused
and documented. Import `cfg` for centralized configuration.

#### `cfg.py` - Global Configuration

```python
# Environment setting
env = None  # Could be 'dev' or 'prod'
do_preprocess = True

# Date parameters
import datetime
dt_start = datetime.date(2010, 1, 1)
dt_end = datetime.date(2020, 1, 1)
```

Best practices: keep global settings here (environment, dates, feature flags);
handle missing credentials gracefully; keep workflow-specific parameters
separate (see `flow_params.py`).

#### `flow_params.py` - Workflow Parameters

```python
import cfg

params = dict()

# Example parameters (commented out)
'''
params['transformx'] = 'zscore'
params['transformy'] = 'rank'
params['regularize'] = True
'''
```

Best practices: define all task parameters here; can reference `cfg.py` values
(e.g. `params['env'] = cfg.env`); comment/uncomment combinations for
experiments. Keep separate from `cfg.py` for clarity.

Why separate `cfg.py` and `flow_params.py`?
- `cfg.py`: Global settings (environment, credentials, dates)
- `flow_params.py`: Workflow-specific task parameters
- Easier to manage multiple workflows or parameter sets

#### `flow.py` - Workflow Instance

Defines the workflow instance imported by other scripts.

Best practices: define once, import everywhere; easy to switch between final
tasks; centralizes workflow configuration. Other scripts just need
`from flow import flow`. DRY principle; consistency across `run.py`,
`visualize.py`, `visualize.ipynb`; easy switching by changing the `task`
variable.

#### `run.py` - Execute Workflow

```python
import d6tflow
import cfg, tasks

from flow import flow

# Optional: Reset tasks to force re-run
# flow.reset(tasks.GetData)

flow.preview()   # Preview what will run
flow.run()       # Execute workflow
```

Usage: `python run.py`. Keep this file simple - import flow and run. Use
`flow.preview()` first. Comment out `flow.reset()` (uncomment to force re-run).
Can create multiple run scripts (e.g. `run_training.py`, `run_prediction.py`).

#### `visualize.py` - Analysis Script

Use workflow outputs for analysis, reporting, or visualization. Organized as
functions for reusability. Import `flow` from `flow.py`; use
`flow.outputLoad(TaskName)` to load specific outputs; do not re-run the workflow
here, just load and analyze; export results (plots, tables, reports).

#### `visualize.ipynb` - Jupyter Notebook

Interactive exploratory analysis using workflow outputs; structure similar to
`visualize.py`. Import `flow` from `flow.py`; comment out `flow.run()` (run via
`run.py` first); keep cells independent for easy re-running; convert
production-ready analysis to `visualize.py` for reproducibility.

#### `.creds.yaml` - Protected Credentials (Optional)

```yaml
# .creds.yaml
api_key: "your-api-key-here"
```

IMPORTANT: add `.creds.yaml` to `.gitignore` immediately; never commit
credentials; provide a `.creds.yaml.example` template; environment variables are
an alternative.

Loading in `cfg.py`:
```python
import yaml
try:
    with open('.creds.yaml') as fh:
        cfg_yaml = yaml.safe_load(fh)
except FileNotFoundError:
    cfg_yaml = {}
```

Using in tasks:
```python
import cfg

class DownloadData(d6tflow.tasks.TaskPqPandas):
    def run(self):
        api_key = cfg.cfg_yaml.get('api_key')
        # Use api_key to fetch data
```

### How the Files Work Together

```
1. cfg.py (Global Config)
   -> 2. flow_params.py (imports cfg)
   -> 3. tasks.py (imports cfg)
   -> 4. flow.py (imports cfg, tasks, flow_params)
   -> 5. run.py, visualize.py, visualize.ipynb (all import flow)
```

Benefits: consistency (same workflow instance everywhere), DRY (define once),
flexibility (easy to switch tasks/parameters), clarity (separation of concerns).

### Alternative Structures

Large projects with multiple modules:
```
project/
|-- tasks/
|   |-- __init__.py
|   |-- etl.py          # ETL tasks
|   |-- features.py     # Feature engineering tasks
|   `-- models.py       # Model training tasks
|-- cfg.py
|-- run.py
|-- visualize.py
`-- utils/
    |-- __init__.py
    |-- data_validation.py
    `-- plotting.py
```

Multiple workflows:
```
project/
|-- tasks.py
|-- cfg.py
|-- flow_params_train.py    # Training parameters
|-- flow_params_predict.py  # Prediction parameters
|-- flow_train.py           # Training workflow
|-- flow_predict.py         # Prediction workflow
|-- run_train.py            # Run training pipeline
|-- run_predict.py          # Run prediction pipeline
`-- visualize_models.py
```

```python
# flow_train.py
from flow_params_train import params
task = tasks.TrainModel
flow = d6tflow.Workflow(task=task, params=params)

# flow_predict.py
from flow_params_predict import params
task = tasks.MakePredictions
flow = d6tflow.Workflow(task=task, params=params)

# run_train.py
from flow_train import flow
flow.run()

# run_predict.py
from flow_predict import flow
flow.run()
```

---

## Additional Resources

- Official docs: https://d6tflow.readthedocs.io/
- GitHub: https://github.com/d6t/d6tflow

---

## Summary

d6tflow: Reproducible, cacheable data science workflows. Tasks (classes with
`run()`), dependencies (`@d6tflow.requires()`), parameters (task variants),
auto-caching, multiple outputs (`persist`), metadata (models/configs).

**Use for**: Multi-step pipelines, ML workflows, reproducible research.
**Avoid for**: Simple scripts, real-time systems, single-step processes.

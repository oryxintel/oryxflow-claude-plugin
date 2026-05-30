# d6tflow Template Project Guide

## What This Template Provides

This is a **minimal, ready-to-use template** for d6tflow projects. It demonstrates the recommended project structure and file organization patterns, with simple example tasks that you'll replace with your actual workflow.

## Template Structure

### Configuration Files

**`cfg.py`** - Global Configuration
- Environment settings (`env`: 'dev' or 'prod')
- Feature flags (`do_preprocess`)
- Date ranges (`dt_start`, `dt_end`)
- Credential loading from `.creds.yaml`

```python
env = None  # 'dev' or 'prod'
do_preprocess = True
dt_start = datetime.date(2010, 1, 1)
dt_end = datetime.date(2020, 1, 1)
```

**`flow_params.py`** - Workflow Parameters
- Task-specific parameters as a dictionary
- Examples provided (commented out) for common ML parameters
- Separate from global config for clarity

```python
params = dict()
# Add your workflow parameters here
# params['model'] = 'lgbm'
# params['regularize'] = True
```

**Why separate?**
- `cfg.py`: Settings that apply across all workflows
- `flow_params.py`: Parameters specific to task execution

### Workflow Files

**`flow.py`** - Workflow Instance
- Defines the workflow once, imported everywhere
- Easy to switch between different final tasks
- Single source of truth

```python
import d6tflow
import cfg, tasks
from flow_params import params

task = tasks.Process  # Switch to tasks.GetData for different workflow
flow = d6tflow.Workflow(task=task, params=params, env=cfg.env)
```

**`tasks.py`** - Task Definitions
- Contains all workflow task classes
- Example tasks: `GetData` → `Process`
- Replace with your actual tasks

**`run.py`** - Execution Script
- Imports and runs the workflow
- Optional reset calls for forcing re-runs
- Preview before execution

```python
from flow import flow
# flow.reset(tasks.GetData)  # Uncomment to force re-run
flow.preview()
flow.run()
```

### Analysis Files

**`visualize.py`** - Analysis Functions
- Organized as reusable functions
- Loads outputs using `flow.outputLoad()`
- For production-ready analysis

**`visualize.ipynb`** - Interactive Notebook
- Exploratory data analysis
- Uses same `flow` instance as other scripts
- Typically don't run workflow here, just load outputs

## Example Tasks Explained

### GetData Task
```python
class GetData(d6tflow.tasks.TaskPqPandas):
    def run(self):
        df = pd.DataFrame({'a': range(10)})
        self.save(df)
```

**Purpose**: Demonstrates basic task structure
- Generates simple sample data
- Shows how to save DataFrame outputs
- Replace with your actual data loading logic

### Process Task
```python
@d6tflow.requires(GetData)
class Process(d6tflow.tasks.TaskPqPandas):
    optional = d6tflow.BoolParameter(default=False)

    def run(self):
        df = self.input().load()
        if self.optional:
            df = df * 2
        self.save(df)
```

**Purpose**: Demonstrates dependencies and parameters
- Depends on `GetData`
- Shows parameter usage
- Shows how to load from upstream tasks
- Replace with your actual processing logic

## How to Customize for Your Project

### 1. Define Your Tasks

Replace the example tasks in `tasks.py` with your actual workflow:

```python
import d6tflow
import pandas as pd
import cfg

class LoadRawData(d6tflow.tasks.TaskPqPandas):
    """
    Load raw data from CSV/database
    """
    def run(self):
        df = pd.read_csv('path/to/data.csv')
        self.save(df)

@d6tflow.requires(LoadRawData)
class CleanData(d6tflow.tasks.TaskPqPandas):
    """
    Clean and validate data
    """
    def run(self):
        df = self.input().load()
        df_clean = df.dropna()
        # Add validation assertions
        assert df_clean.shape[0] > 0, "Empty dataframe after cleaning"
        self.save(df_clean)

@d6tflow.requires(CleanData)
class FeatureEngineering(d6tflow.tasks.TaskPqPandas):
    """
    Create features for modeling
    """
    def run(self):
        df = self.input().load()
        # Add your feature engineering logic
        self.save(df)
```

### 2. Add Parameters

Define workflow parameters in `flow_params.py`:

```python
import cfg

params = {
    'date': '2024-01-01',
    'model_type': 'lgbm',
    'test_size': 0.2,
    'n_estimators': 100
}
```

Use parameters in tasks:

```python
class TrainModel(d6tflow.tasks.TaskPickle):
    model_type = d6tflow.Parameter()
    n_estimators = d6tflow.IntParameter()

    def run(self):
        # Use self.model_type, self.n_estimators
        pass
```

### 3. Set the Final Task

Update `flow.py` to use your final task:

```python
from flow_params import params
import tasks

task = tasks.FeatureEngineering  # Your final task
flow = d6tflow.Workflow(task=task, params=params, env=cfg.env)
```

### 4. Configure Analysis

Update `visualize.py` with your analysis functions:

```python
from flow import flow
import tasks

def analyze_features():
    df = flow.outputLoad(tasks.FeatureEngineering)
    # Your analysis here
    print(df.describe())

analyze_features()
```

## Development Workflow

### 1. Start with Dev Mode

Use environment-specific settings for faster iteration:

```python
# In cfg.py
env = 'dev'

# In tasks, use conditionally
if self.env == 'dev':
    df = df.sample(1000)  # Use subset in dev
```

### 2. Iterate on Tasks

```python
# Modify a task in tasks.py
# Then in run.py or Python REPL:
from flow import flow
flow.reset(tasks.TaskName)  # Force re-run from this task
flow.run()
```

### 3. Inspect Outputs

```python
from flow import flow
import tasks

# Preview what will run
flow.preview()

# Load specific task output
df = flow.outputLoad(tasks.CleanData)
print(df.head())
print(df.info())
```

### 4. Test End-to-End

```bash
# Run full workflow
python run.py

# Analyze results
python visualize.py
```

## Best Practices for This Template

### ✅ Do

1. **Keep the file structure** - Don't combine files
2. **Use the flow pattern** - Import `from flow import flow` everywhere
3. **Add docstrings** to all new tasks
4. **Use assertions** to validate data at each step
5. **Test in dev mode** before running on full data
6. **Document parameters** in `flow_params.py` with comments
7. **Keep credentials in `.creds.yaml`** (not committed to git)

### ❌ Don't

1. **Don't hardcode parameters** in tasks - use `flow_params.py`
2. **Don't create workflow instances** in multiple places - use `flow.py`
3. **Don't skip validation** - add assertions for data contracts
4. **Don't commit `.creds.yaml`** - add to `.gitignore` immediately
5. **Don't run workflows in notebooks** - use `run.py`, load outputs in notebooks

## Credentials Management

### Setup `.creds.yaml` (Optional)

```yaml
# .creds.yaml (DO NOT COMMIT)
api_key: "your-api-key"
db_password: "your-password"
```

### Create `.creds.yaml.example`

```yaml
# .creds.yaml.example (COMMIT THIS)
api_key: "your-api-key-here"
db_password: "your-password-here"
```

### Load in cfg.py

```python
try:
    import yaml
    with open('.creds.yaml') as fh:
        cfg_creds = yaml.safe_load(fh)
except FileNotFoundError:
    cfg_creds = {}
    print("Warning: .creds.yaml not found")
```

### Use in tasks

```python
import cfg

class DownloadData(d6tflow.tasks.TaskPqPandas):
    def run(self):
        api_key = cfg.cfg_creds.get('api_key')
        # Use api_key to fetch data
```

## Version Control

### Add to .gitignore

```gitignore
# Credentials
.creds.yaml
*.key

# Data
data/
*.csv
*.parquet

# d6tflow cache
.d6tflow/

# Python
__pycache__/
*.pyc
.ipynb_checkpoints/

# Outputs
outputs/
plots/
*.png
```

### Commit to Git

- ✅ `tasks.py`, `cfg.py`, `flow_params.py`, `flow.py`
- ✅ `run.py`, `visualize.py`, `visualize.ipynb`
- ✅ `CLAUDE.md`, `claude-d6tflow.md`, `claude-project.md`
- ✅ `.creds.yaml.example`
- ❌ `.creds.yaml`, `data/`, `.d6tflow/`

## Scaling to Larger Projects

### Multiple Task Files

```
project/
├── tasks/
│   ├── __init__.py
│   ├── etl.py
│   ├── features.py
│   └── models.py
├── flow.py
└── run.py
```

```python
# flow.py
from tasks.models import TrainModel
flow = d6tflow.Workflow(task=TrainModel, params=params)
```

### Multiple Workflows

```
project/
├── tasks.py
├── flow_params_train.py
├── flow_params_predict.py
├── flow_train.py
├── flow_predict.py
├── run_train.py
└── run_predict.py
```

## Template-Specific Tips

### Using the Template Files

- **Replace `GetData` and `Process`** with your actual task classes
- **Keep the file structure** - it's designed for clarity and maintainability
- **Use `flow.py`** as the single source of truth for your workflow
- **Start simple** - add complexity incrementally

### Quick Troubleshooting

- **Task not re-running?** Use `flow.reset(tasks.TaskName)` to force re-run
- **Import errors?** Ensure you're in the project directory
- **Need d6tflow help?** See `@claude-d6tflow.md` for comprehensive patterns

## Next Steps

1. **Review the d6tflow guide** (`@claude-d6tflow.md`) for comprehensive documentation
2. **Replace example tasks** with your actual workflow logic
3. **Define parameters** in `flow_params.py`
4. **Test in dev mode** for fast iteration
5. **Add validation** with assertions
6. **Document your tasks** with docstrings
7. **Run and analyze** using `run.py` and `visualize.py`

This template gives you a solid foundation - now build your workflow on top of it!

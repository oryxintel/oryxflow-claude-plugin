# d6tflow Conventions: How We Organize a Project

House conventions loaded on demand by the `d6tflow` skill - the project layout,
how to group supporting code, and how to name things. This is the "house style"
companion to [reference.md](reference.md) (the library API). The library tells
you how d6tflow WORKS; this tells you how to ORGANIZE a project so it - and the
AI agent working in it - stays accurate as it grows.

---

## Naming: one principle behind all of it

One idea drives every naming rule below: **a name is something the reader (you,
me, the next session) has to hold and can mis-apply, so every convention pushes
the same direction - fewer translation layers, self-describing tokens, and
shared prefixes that turn scattered names into recognizable families.** A wrong-
column or wrong-variable bug starts as a name you had to translate in your head
and got wrong. The rules for columns, tasks, and variables are the SAME rule
applied to different identifiers; when a case below is not spelled out, decide it
by that principle.

### Column naming: carry one canonical name

Every rename is a mapping a reader must hold and can mis-apply; a round-trip (raw
code -> display -> code) is pure cost and a classic wrong-column bug. Minimize the
layers:

- **One canonical name per column, carried end to end.** Rename raw source codes to
  canonical ONCE, in the loader / source task; never re-alias downstream. Canonical
  is `descriptive_snake_case` (`rate_construction`, not `uc_rate` or
  `Under Construction Rate`) - self-describing (no data-doc lookup to know what it
  is) AND code-safe (attribute access, no fragile spaces / mixed case).
- **Order tokens broad -> narrow** (category first), the OPPOSITE of English word
  order, so columns in one family share a leading prefix and cluster - for a reader
  and for `df.filter(like='rate_')`: `rate_construction`, `rate_completion`,
  `rate_availability` (not `construction_rate`, nor the English "under construction
  rate"); `return_capital`, `return_income`, `return_total`; `price_open`,
  `price_high`, `price_low`. English order is for the DISPLAY label only.
- **Pretty labels live ONLY at the plotting layer.** `viz/<subject>.py` maps
  canonical -> Human-readable Title Case for axes/legends (`rate_construction` ->
  "Construction"). Never a second DATA-level rename.
- **Derive by suffixing the source name** with a small, fixed vocabulary, so the
  name carries provenance AND transform: `_yoy` (YoY growth ratio), `_yoy_pp` /
  `_diff` (pp difference), `_pct`, `_ma{n}`, `_lag{n}`, `_roll{n}`, `_z`, `_log`.
  The operation goes LAST (narrowest qualifier): `rate_construction_yoy` then reads
  as exactly what it is and where it came from. Disambiguate the FORM when a column
  could be read two ways (growth vs pp-difference) - name the unit (`_pp` vs
  `_pct`); do not hide two operations behind a vague `_chg`.
- **Do not shadow a supplied series.** If the source already ships a derived series
  (e.g. an as-supplied YoY), use it; a cross-check derivation is named as a check
  and dropped once verified, not left to compete with the canonical column.
- **Record the canonical set + the raw->canonical map in `docs/d6tflow-data.md`,**
  and use canonical names in the task docstring's `Out:` contract - the one place
  that answers "what is this column." Keep the suffix vocabulary small and listed
  there (like concept-module names), so `_chg` and `_diff` do not both appear for
  the same operation.

### Task naming: name for the output, broad -> narrow

Name a task for the OUTPUT it produces (a noun: `OEWSWages`, `CleanedSales`,
`TrainedModel`, `DataOEWS`), not the verb it performs - the output is what
downstream code and the cache are keyed on. Avoid generic names (`GetData`,
`LoadData`, `Process`, `Run`); they say nothing about the output and collide
across projects. For a task that loads/produces a named dataset, `Data<Name>`
(`DataOEWS`) or a plain `<Name>` (`OEWS`) are both fine.

Order the name broad -> narrow (same rule as columns) so tasks in a family share a
leading token and cluster in `tasks.py` / `flow.preview()` / `data/`:
`FundamentalsAll`, `FundamentalsSignals`, `FundamentalsLeadLag` (NOT
`LeadLagAnalysis`); loaders share the `Data<Name>` prefix.

### DataFrame / variable naming

Same rule for `df` and variable names. Name for content, broad -> narrow, sharing a
prefix across a family or a task's parameter variants: `df_profile_division` /
`df_profile_cbsa` (variant last, so `df_profile_*` cluster), not `df_div_profile`.
A bare `df` is fine for a single local frame; keep the established ML idioms
(`df_X`, `df_y`, `df_train`, `df_test`).

---

## Code organization: group by subject (eda / utils / viz)

The flat starter (`tasks.py` + `visualize.py` + ad-hoc `eda/`) stops scaling once
a project has many tasks plus reusable helpers and plots. Group supporting code by
the SUBJECT it concerns - a task, a dataset, or a cross-cutting concept -
mirroring how the pipeline is keyed on tasks, so a reader finds a subject's
probes, helpers, and figures by name.

Three buckets:

- `eda/<subject>/<name>.py` - READ-ONLY test / exploration / verification probes
  (the no-inline-Python destination). Each `eda/<subject>/` is a package: add an
  `__init__.py` and run probes as `python -m eda.<subject>.<name>` from the root.
- `utils/` - helpers. `utils/<subject>.py` for one subject's helpers;
  `utils/__init__.py` only for truly generic, subject-less helpers.
- `viz/` - plotting. `viz/<subject>.py` exposes that subject's figures (e.g.
  `build_map(metro)`); `viz/__init__.py` only for generic plotting helpers
  (palettes, save/format). The starter `visualize.py` graduates into `viz/` once
  you have per-subject or shared plotting.

```
eda/
  data_oews/
    verify_coercion.py
    inspect_fields.py
  msa50_map/                 # a DATASET subject (reference data, not a task)
    validate_coverage.py
utils/
  __init__.py                # truly generic, subject-less helpers (often empty)
  geo.py                     # concept module: shared by ACS + AreaGeometry
  acs_residence_occupation.py  # one task's helpers (# task: ACSResidenceOccupation)
viz/
  __init__.py                # SEQUENTIAL_PALETTE, save_html() - imports no task
  residence_exposure.py      # build_map(metro)   (# task: ResidenceExposure)
```

### Rules

- **Subject = task, dataset, or concept.** Most code is about a task (snake_case
  of the task class). Code about a reference / source dataset, or a cross-cutting
  concept (geo, dates, io), groups under that name (`eda/msa50_map/`,
  `utils/msa50_map.py`, `utils/geo.py`). Keep the set of concept names small and
  listed somewhere (e.g. in `docs/d6tflow-data.md`) so they are not reinvented
  (`geo`, not also `geography`).
- **Shared helper -> a concept/dataset module (concept by default).** A helper
  used by 2+ subjects (tasks AND/OR eda probes) goes in a CONCEPT or dataset module
  named for the shared idea: `utils/geo.py` for `resolve_metro_geo` / `GEO_LEVELS`
  (shared by ACSResidenceOccupation + AreaGeometry). A helper used by ONE subject,
  extracted only because it is big, goes in that subject's module
  (`utils/<subject>.py`). Only truly generic, subject-less helpers go in
  `__init__.py`. Do not reason about DAG topology; only if a shared helper has no
  natural concept name (rare) fall back to the upstream producer's module.
- **Module casing: snake_case.** Lowercase the task class, underscore at each case
  boundary, each acronym run as one token (`DataOEWS` -> `data_oews`,
  `ACSResidenceOccupation` -> `acs_residence_occupation`). This is NOT fully
  algorithmic for glued-lowercase class names - `EmploymentbyMSA` ->
  `employment_by_msa` (the `by` has no case boundary to split on) - so the SOURCE
  OF TRUTH is a header comment in the subject module / package: `# task:
  EmploymentbyMSA`. Prefer clean class names (`EmploymentByMSA`) going forward so
  the conversion is trivial; record any non-obvious mapping next to the code.
- **Name files for the specific thing they do**, never a bare verb. The folder
  already names the subject, so DROP the redundant subject token and name the
  aspect: `eda/data_oews/verify_coercion.py` (not `verify_dataoews.py`, not bare
  `verify.py`). This holds even when a folder has a single probe - a specific name
  future-proofs the second one.
- **`eda/` produces no PIPELINE artifacts.** A probe inspects and asserts; it must
  not write a task-output-shaped file into `data/`. Code that PRODUCES a `data/`
  artifact downstream consumes is a builder, not a probe (see edge cases). The one
  thing a probe MAY write is disposable scratch (cache an expensive pull while
  iterating, dump an intermediate to eyeball) - and that goes to
  `data/.eda/<subject>/`, never beside task outputs. See "Scratch for probes".
- **Extract on the SECOND use** (or when a single-use helper is large enough to
  clutter the task). A one-off constant used by one task stays inline in
  `tasks.py`; do not spin up a near-empty module per task.
- **Keep `__init__.py` for truly generic, subject-less helpers only** so
  `utils/__init__.py` / `viz/__init__.py` do not become junk drawers.

### Import contract

Subject modules import project modules (`import tasks`, `from flow import flow`),
so they resolve ONLY as `python -m <pkg>.<...>` from the project root - bare
`python viz/x.py` fails with `ModuleNotFoundError: tasks`. Two requirements:

- every `eda/`, `eda/<subject>/`, `utils/`, `viz/` needs an `__init__.py`;
- a package `__init__.py` (`utils/__init__.py`, `viz/__init__.py`) must NOT import
  any task at module load - importing the package for one generic helper would
  otherwise drag in the whole DAG. Task imports belong in the per-subject module,
  not the package root.

### Edge cases

- **Code that LOADS or builds a `data/` input.** Loading external data is the
  idiomatic loader-task pattern (`Data<Name>`, see "Task naming"), so an external,
  reproducible builder (geo maps / crosswalks from Census/OMB files) should be a
  real d6tflow SOURCE TASK BY DEFAULT - in the DAG, cached, reset-able, and read
  downstream via `inputLoad()` instead of re-reading a csv. A plain `build_*.py`
  that fetches an external source and writes a `data/` csv is just a loader task
  that has not been written as one yet. Two exceptions keep it a loader/maintenance
  SCRIPT instead of a task: (1) HAND-CURATED data (dedupe/clean an author-built
  csv) - not reproducible from a source, so calling it a "task" is misleading; (2)
  the output is not something a d6tflow task type stores well - not a DataFrame
  (TaskPqPandas) or a serializable object (TaskPickle/TaskJson), e.g. a raw file
  asset or a directory of files - where a task buys little. Such a script lives
  under the dataset (`utils/<dataset>.py`, run via `python -m`, named for what it
  rebuilds), not in `eda/` (it writes).
- **Non-task reference data** (e.g. `msa50_map`): group probes under the dataset -
  `eda/msa50_map/validate_coverage.py`, helpers in `utils/msa50_map.py`.
- **A probe spanning two subjects.** Primary subject = what it INVESTIGATES (not
  where it reads input); file it there and note the secondary in a comment. If it
  genuinely splits 50/50 (e.g. validates an ACS path AND a geometry path), file it
  under their shared CONCEPT folder (`eda/geo/`, `eda/coverage/`) rather than
  picking a task arbitrarily.
- **Probes/tests for `viz/` code are not special**: group under the subject the
  figure is about (`eda/<subject>/`); there is no `eda/viz/` bucket.
- **Graduating a root module** (`visualize.py` -> `viz/<subject>.py`): MOVE it
  (delete the original) in the same change, or the two copies drift.
- **Stale caches on rename.** Renaming/deleting a task orphans its
  `data/<OldName>/` cache (and `__pycache__`); subject-grouping won't reap it -
  delete the stale cache when you rename a task.

### Scratch for probes

Sometimes a probe genuinely needs to persist intermediate data to do its job -
cache an expensive download while you iterate on a verification, or dump a
reshaped frame to eyeball it. That is fine, but it is NOT a `data/<Task>/` output.
Write it to `data/.eda/<subject>/` (mirroring the `eda/<subject>/` code layout)
and treat it as regenerable.

Why there: the leading-dot dir is gitignored by the `.*` rule, which sits OUTSIDE
the data-files block that `init-gitlfs` un-comments - so the scratch stays
untracked even in a project that LFS-tracks `data/`. It can never be committed by
accident, and the dot keeps it visually distinct from task-output dirs.

The decision before "where": a finding -> print it + record in
`docs/d6tflow-data.md` (no file). A derived dataset worth reusing downstream -> a
TASK (`self.save`), not scratch. Genuinely throwaway intermediate -> `data/.eda/`.

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
|-- viz-template.ipynb # Report-notebook template; copy to viz-<topic>.ipynb
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
4. **Analysis Layer** (`visualize.py` + `viz-<topic>.ipynb` report notebooks): Load
   and analyze outputs

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
(e.g. `params['env'] = cfg.env`); comment/uncomment combinations for experiments.
Keep separate from `cfg.py` (global settings vs workflow params) so multiple
workflows / parameter sets stay easy to manage.

#### `flow.py` - Workflow Instance

Defines the workflow instance imported by other scripts. Define once, import
everywhere (`from flow import flow`); switch final tasks by changing the `task`
variable. (Rationale under "How the Files Work Together".)

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

#### `viz-template.ipynb` - report-notebook template

The scaffold's report-notebook starting point. Don't edit it in place: copy it to
`viz-<topic>.ipynb` at the project root (one report = one notebook, named for its
subject) and author the copy; the template stays pristine. Import `flow` from
`flow.py`; comment out `flow.run()` (run via `run.py` first); keep cells
independent for easy re-running. Edit cells with the `NotebookEdit` tool, not by
hand-writing JSON. Render to `reports/render/` (see SKILL.md "Render / publish a
notebook"); convert production-ready analysis to `visualize.py` for reproducibility.

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
   -> 5. run.py, visualize.py, viz-<topic>.ipynb (all import flow)
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

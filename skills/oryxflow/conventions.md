# oryxflow Conventions: How to Organize a Project

House conventions loaded on demand by the `oryxflow` skill - the project layout,
how to group supporting code, and how to name things. This is the "house style"
companion to [reference.md](reference.md) (the library API). reference.md tells
you how oryxflow WORKS; this tells you how to ORGANIZE a project so it stays
accurate as you build and grow it.

---

## Naming: one principle behind all of it

One idea drives every naming rule below: **a name is something the reader (you,
the next session) has to hold and can mis-apply, so every convention pushes
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
  is `descriptive_snake_case` (`yield_dividend`, not `div_yld` or
  `Dividend Yield`) - self-describing (no data-doc lookup to know what it
  is) AND code-safe (attribute access, no fragile spaces / mixed case).
- **Order tokens broad -> narrow** (category first), the OPPOSITE of English word
  order, so columns in one family share a leading prefix and cluster - for a reader
  and for `df.filter(like='yield_')`: `yield_dividend`, `yield_earnings`,
  `yield_fcf` (not `dividend_yield`, nor the English "dividend yield");
  `return_capital`, `return_income`, `return_total`; `price_open`,
  `price_high`, `price_low`. English order is for the DISPLAY label only.
- **Name a derived metric for WHAT IT MEASURES, not just its unit.** The domain
  word is the most-searched token and must be IN the name: `win_rate`,
  `benchmark_coverage_pct` (share of benchmark constituents held), not `pct_wins`
  or `pct_covered` - and never a bare unit/stat PREFIX (`pct_x`, `avg_x`) that
  hides which metric it is and scatters a family under the unit instead of the
  subject. Same broad->narrow rule: subject first, unit/operation last (next
  bullet). A whole count/ratio family should share ONE stem so the arithmetic
  reads from the names - see the worked family after the Don't/Do table.
- **Pretty labels live ONLY at the plotting layer.** `viz/<subject>.py` maps
  canonical -> Human-readable Title Case for axes/legends (`yield_dividend` ->
  "Dividend Yield"). Never a second DATA-level rename.
- **Derive by suffixing the source name** with a small, fixed vocabulary, so the
  name carries provenance AND transform: `_yoy` (YoY growth ratio), `_yoy_pp` /
  `_diff` (pp difference), `_pct`, `_ma{n}`, `_lag{n}`, `_roll{n}`, `_z`, `_log`;
  unit tags (`_usd`, `_local`, `_eur`); and aggregations over a series (`_avg`,
  `_min`, `_max`, `_median`, `_std`). The operation goes LAST (narrowest
  qualifier): `yield_dividend_yoy` then reads as exactly what it is and where it
  came from. When several suffixes stack, order them innermost->outermost =
  transform, unit, aggregation - so an aggregation stat is the OUTERMOST suffix
  (it wraps the whole metric) and sibling stats of one metric sort adjacently:
  `benchmark_coverage_pct_avg` / `_min` / `_max`, `return_yoy_usd_avg`. NEVER a
  leading `avg_`/`min_` prefix (see the metric-naming bullet). Disambiguate the
  FORM when a column could be read two ways (growth vs pp-difference) - name the
  unit (`_pp` vs `_pct`); do not hide two operations behind a vague `_chg`.
- **Do not shadow a supplied series.** If the source already ships a derived series
  (e.g. an as-supplied YoY), use it; a cross-check derivation is named as a check
  and dropped once verified, not left to compete with the canonical column.
- **Record the canonical set + the raw->canonical map in `docs/oryxflow-data.md`,**
  and use canonical names in the task docstring's `Out:` contract - the one place
  that answers "what is this column." Keep the suffix vocabulary small and listed
  there (like concept-module names), so `_chg` and `_diff` do not both appear for
  the same operation.

**Don't / Do (the one trap: a leading stat/unit vs a leading subject).** A stat or
unit as a LEADING prefix is the wrong-way-round default that pandas `.agg()` habit
produces; move it to a suffix. This is NOT the same as a leading SUBJECT word (a
family prefix like `yield_`, `price_`, `return_`), which is correct - the subject
leads, the operation trails:

| Don't (stat/unit prefix)        | Do (subject leads, stat/unit trails) | Why                                  |
|---------------------------------|--------------------------------------|--------------------------------------|
| `avg_position_value`            | `position_value_avg`                 | stat is the outermost suffix         |
| `pct_wins`                      | `win_rate`                           | subject first; `pct_` hides the metric |
| `n_holdings` / `count_holdings` | `holdings_count`                     | count is a unit suffix, not a prefix |
| `min_price`                     | `price_min`                          | stat suffix                          |
| `avg_coverage_pct`              | `benchmark_coverage_pct_avg`         | stack innermost->outermost: metric, unit, stat |

Contrast - these leading tokens are CORRECT because the token is the subject, not a
stat: `yield_dividend` / `yield_earnings` (family word `yield` leads),
`price_open` / `price_high`, `return_capital` / `return_total`. The test: if the
leading token names WHAT the column is (a subject family), it leads; if it names an
OPERATION on some other subject (`avg`, `pct`, `n`, `count`, `min`, `max`, `sum`,
`median`, `std`), it is a suffix.

**A worked family** (a count/ratio triple - e.g. a benchmark-coverage analysis:
what share of the benchmark's constituents does the portfolio hold?) shows both
ideas at once - the numerator, denominator, and ratio are ONE family that share
the SAME leading token, and the ratio is named for the analysis's PURPOSE:

| role              | column                    |
|-------------------|---------------------------|
| denominator count | `benchmark_total`         |
| numerator count   | `benchmark_covered`       |
| headline metric   | `benchmark_coverage_pct` (= covered / total) |

The leading token is the SUBJECT the counts are about (`benchmark`), so the ratio
inherits it: the shape is `{subject}_{concept}_{unit}`. That is what the `*`
stands for in `*_coverage_pct` / `*_churn_rate` - the count's subject, not a blank
slot: `user_churn_rate` because the counts are `users_total` / `users_churned`;
`submarket_coverage_pct` because the counts are `submarkets_total` /
`submarkets_covered`. Subject leads because the counts inherently do (a count OF
users), and the ratio must match its own counts to cluster. Reading
`benchmark_coverage_pct = benchmark_covered / benchmark_total` straight off the
names is the payoff.

Keep all three on ONE leading token; the anti-pattern is a mixed grammar where no
two columns relate on their face (`benchmark_total`, `names_with_data`,
`pct_covered` - three shapes, headline metric hidden behind a bare `pct_`). Pick
one word for the concept (`covered` for the count, `coverage` for the ratio) and
reuse it. Lead with the PURPOSE instead (`churn_*` / `coverage_*`) only when the
purpose is the top-level key you group a whole multi-subject analysis by - and
then commit ALL three to it (`churn_users_total` / `churn_users_churned` /
`churn_users_rate`), never a mix like `churn_users_total` + `churn_rate`.

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
prefix across a family or a task's parameter variants: `df_returns_gross` /
`df_returns_net` (variant last, so `df_returns_*` cluster), not `df_gross_returns`.
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
- `utils/` - helpers that EARNED extraction (large/complex, or shared by 2+
  tasks - see "Task logic belongs in the task" below). `utils/<subject>.py` for one
  subject's helpers; `utils/__init__.py` only for truly generic, subject-less ones.
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
  listed somewhere (e.g. in `docs/oryxflow-data.md`) so they are not reinvented
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
  clutter the task) - full rule below. A one-off constant used by one task stays
  inline in `tasks.py`; do not spin up a near-empty module per task.
- **Keep `__init__.py` for truly generic, subject-less helpers only** so
  `utils/__init__.py` / `viz/__init__.py` do not become junk drawers.

### Task logic belongs in the task

A task's `run()` is where its logic lives. Reading a source, parsing, renaming
columns, coercing dtypes, cleaning - all of it goes in the body, however
unglamorous. The smell is a `run()` that is one call into a project module plus
logging and asserts:

```python
def run(self):
    df = benchmark.read_returns(cfg.file_returns)   # <- the task, elsewhere
    self.logger.info("rows={}", len(df))
    self.save(df)
```

The task is now a wrapper around the thing a reader came to read, and the module
is a private detail of one task with a public-looking name. Inline it.

**Extract only on one of two triggers**: the logic is LARGE or complex enough to
clutter the task (a real algorithm, not a load-and-tidy), or 2+ TASKS use it.
Nothing else qualifies. Two rationalizations to reject by name:

- **"An `eda/` probe needs it."** That is an argument AGAINST extracting. A probe
  that imports the helper re-runs ingestion outside the DAG: uncached, and free to
  drift from what the task actually saved (different source file, different code
  state), so the probe verifies something no downstream task ever saw. The probe
  should read the task's OUTPUT - `flow.outputLoad(tasks.ReturnsBenchmark)`.
  Needing the helper is usually the signal the probe is bypassing the task; fix
  the probe, not the layout. (A probe that must run BEFORE the task exists is fine - it is
  throwaway, and the logic lands in the task afterwards.)
- **"I need to iterate on the logic."** Editing `run()` in place already iterates:
  auto invalidation reruns that task and its downstream on the next `python run.py`
  (see the skill's "Code-aware invalidation"). To compare versions directly rather
  than overwrite, pin `code_version = 'v1-baseline'` plus `keep_versions = True`,
  which keeps old outputs at readable paths (`data/Task/v1-baseline/...`).
  Extraction buys nothing here.

When you inline a helper, CARRY ITS COMMENTS. The reason a helper accumulates is
often a hard-won quirk ("the export reads the id column as a float when any row is
blank, so `14454` becomes `14454.0` and every join breaks silently") - that
sentence is the most valuable thing in the file. It belongs in the task docstring
(if it is part of the in -> out contract) or inline at the line it explains. Losing
it is a worse outcome than the original layout.

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
  real oryxflow SOURCE TASK BY DEFAULT - in the DAG, cached, reset-able, and read
  downstream via `inputLoad()` instead of re-reading a csv. A plain `build_*.py`
  that fetches an external source and writes a `data/` csv is just a loader task
  that has not been written as one yet. Two exceptions keep it a loader/maintenance
  SCRIPT instead of a task: (1) HAND-CURATED data (dedupe/clean an author-built
  csv) - not reproducible from a source, so calling it a "task" is misleading; (2)
  the output is not something a oryxflow task type stores well - not a DataFrame
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
`docs/oryxflow-data.md` (no file). A derived dataset worth reusing downstream -> a
TASK (`self.save`), not scratch. Genuinely throwaway intermediate -> `data/.eda/`.

---

## Project Structure (deep dive)

oryxflow projects follow a standard file organization that separates concerns.

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
import oryxflow
import pandas as pd
import cfg

class GetData(oryxflow.tasks.TaskPqPandas):
    """Load raw data"""
    def run(self):
        df = pd.DataFrame({'a': range(10)})
        self.save(df)

@oryxflow.requires(GetData)
class Process(oryxflow.tasks.TaskPqPandas):
    """Process the raw data"""
    optional = oryxflow.BoolParameter(default=False)

    def run(self):
        df = self.input().load()
        if self.optional:
            df = df * 2
        self.save(df)
```

Best practices: start with one file and keep it that way far longer than feels
natural - a sectioned single file scales past 500 lines fine. Split into
`tasks_<phase>.py` modules only once it is genuinely long or a separable
subsystem appears; see "Scaling up" below for the full graduated progression.
Keep tasks focused and documented. Import `cfg` for centralized configuration.

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
import oryxflow
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
`viz-<topic>.ipynb` at the project root (one report = one notebook) and author the
copy; the template stays pristine. Name `<topic>` subject-first, with enough
context to read standalone - the rendered `reports/render/viz-<topic>.html` is
consumed DETACHED from the project (emailed, dropped in a channel), so the SUBJECT
must be in the name, not just the analysis type: `viz-benchmark-coverage`, not a
bare `viz-coverage` ("coverage of WHAT" has to survive the file travelling alone).
Infer that subject from what the report is built on - the task names it loads
(`BenchmarkCoverage` -> `benchmark`) or the project's overall purpose - rather
than inventing a new word. Import `flow` from
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

class DownloadData(oryxflow.tasks.TaskPqPandas):
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

## Scaling up: organizing a growing project

Most projects stay flat (one `tasks.py`, `run.py`, `flow.py`,
`flow_params.py`) - that is the right shape for the ~80% that stay
research-only, and the structure above is for them. The ~20% that grow - usually
when something goes to "prod" - graduate along the steps below. Data scientists
are typically weak at code organization, so be PROACTIVE here:
nudge to graduate on a concrete trigger (see SKILL.md "Graduating a growing
project"), restructuring as the project grows rather than over-building up front.

### Scaling `tasks.py` - a graduated progression

Do NOT jump to splitting files. Each step is deferred until the prior one
strains - you keep one file as long as it stays navigable:

- **a. One `tasks.py`, chain-ordered** (the flat start - tasks in DAG order).
- **b. Naming families.** Broad->narrow prefixes (the existing convention:
  `Features*`, `Model*`, `Data*`) cluster related tasks so a branch reads
  together. (See "Task naming".)
- **c. Comment section-header blocks** divide branches/phases WITHIN the one
  file. The cheap intermediate organizer - it carries a file well past ~500
  lines without splitting, and the headers double as orientation and as unique
  edit anchors for you:
  ```python
  # ===========================================================================
  # Model layer - train + evaluate (parallel to the feature layer above)
  # ===========================================================================
  ```
- **d. Split into modules** - only when the file is GENUINELY long (rough signal
  ~1000 lines / ~20+ tasks, or "scrolling to find a task" pain) OR a separable
  subsystem has emerged. Cut along the section seams from step c. This is
  cache-safe: a task's identity is its CLASS NAME (`task_family`), not its module
  path, so moving a class from `tasks.py` to `tasks_model.py` does NOT invalidate
  its `data/<Class>/` cache. (RENAMING a class still orphans the old cache - see
  "Stale caches on rename"; only MOVING is free.)

### Two split axes

When you do split (step d), there are two orthogonal ways to cut:

- **Phase axis** - break up the main pipeline by stage: `tasks_features.py` /
  `tasks_model.py` / `tasks_eval.py`. Each module imports the UPSTREAM phase only
  (`tasks_model` imports `tasks_features`), so the import graph is acyclic by
  construction.
- **Subsystem axis** - carve off a separable concern: a distinct data
  source/platform (`tasks_13f.py`), an app, an LLM/reporting layer. This is the
  "group by subject" rule (above) applied to TASKS. When the subsystem bundles
  its own helpers/config/templates, give it a SUBDIR PACKAGE
  (`llm/tasks_llm.py` + `llm/prompts.py` + ...), matching the `eda/utils/viz`
  by-subject grouping.

### Keep a slim `tasks.py` spine (not a re-export aggregator)

After splitting, `tasks.py` stays - it holds the pipeline-overview module
docstring (the project-goal home this convention mandates) plus the orchestration
tasks (`RunAll`, and a prod twin if any), and it imports the phase modules. The
phase/subsystem modules hold the actual work; a cross-module dependency imports
the specific sibling module directly. Do NOT build an aggregator module that
re-exports every task - direct imports keep the graph acyclic and are what real
projects use.

```python
# tasks.py (the spine, after splitting)
"""<Project goal: what the pipeline produces and why - top-level project doc.>"""
import oryxflow
import cfg
import tasks_features, tasks_model, tasks_eval   # phase modules (the work)

@oryxflow.requires(tasks_eval.ModelEval)
class RunAll(oryxflow.tasks.TaskJson):
    """Run the full pipeline; completion marker."""
    def run(self):
        self.save({'status': 'complete'})
```
```python
# tasks_model.py (a phase module - imports the UPSTREAM phase only -> acyclic)
"""Model layer: train + in-sample performance."""
import oryxflow
import cfg
import tasks_features

@oryxflow.requires(tasks_features.FeaturesTransform)
class ModelTrain(oryxflow.tasks.TaskPqPandas):
    ...
```

### `flow_params.py` keeps experiment AND prod params

`flow.py` / `flow_params.py` are kept at every tier. Put both the experiment
`params` (comment-toggle, last assignment wins) and a frozen `params_prod` dict
in the ONE `flow_params.py` - do not spin up `flow_params_<topic>.py` files
unless the project is genuinely running independent workflows.

```python
# flow_params.py
import cfg

# Experiment params (toggle by commenting; last assignment wins)
params = dict(sector='Residential')
params['model'] = 'rf'
params['env'] = cfg.env
params['period_current'] = '2025Q4'

# Frozen prod params - ONE source of truth, imported by the prod orchestration
params_prod = dict(
    sector='Residential', env='prod', model='rf',
    transformx='chg_yoy_rank', transformy='rankpct', regularize=True,
    period_current=params['period_current'],
)
```

Prod and experiment then coexist in one directory via `env=prod` / `env=dev`
data segregation (`cfg.env`) and a `RunAll...Prod` orchestration task that
imports `params_prod`. That lifecycle - the prod task, selective resets to keep
a model frozen while refreshing data, the periodic-refresh protocol - lives in
[ml-patterns.md](ml-patterns.md) ("Productionizing: prod vs experiment").

### Run tiers by lifecycle (not by topic)

The default project has ONE entrypoint, `run.py` - keep it that way until a
distinct RUN LIFECYCLE appears, then add a sibling named for the lifecycle. Name
by lifecycle, never by topic: lifecycle is a CLOSED set (~3 files); topic is
open and multiplies as registry ENTRIES inside a file, not as new files. That is
what keeps you at ~3 run files instead of 20.

- `run.py` - **experiment** tier (the default, unchanged): the fast inner loop
  on ONE active param set (`params`), edit-and-rerun. Uses `flow.py`'s singleton.
- `run_prod.py` - **prod** tier: frozen `params_prod`, kept outputs, selective
  reset. Runs the frozen deliverable on fresh data.
- `run_eda.py <topic>` - **comparison** tier: run MANY variants at once (heavy
  experiments / A-B) via `WorkflowMulti`; the topic arg selects a registry
  entry. Distinct from `run.py` (one param set, tight loop) - reach here only to
  COMPARE.

`run_prod.py` and `run_eda.py` are GRADUATED add-ons, not part of the minimal
scaffold - copy them from the plugin's `resources/template-prod/` when the
lifecycle appears (the same "defer until it strains" discipline as splitting
`tasks.py`). The ~80% research-only projects never need them.

Two load-bearing points, both general (not ML-specific):

- **Prod builds its Workflow INLINE.** `flow.py` builds a module-level `flow`
  singleton at import, bound to the experiment tier (`cfg.env`, `params`) and
  shared by everything that does `from flow import flow`. It cannot serve two
  tiers at once, so `run_prod.py` constructs its own
  `oryxflow.WorkflowMulti(FinalTask, variants, env='prod')`. (Since `params_prod`
  is one frozen dict, build the named `variants` from it + the prod axis; a single
  frozen run can use plain `oryxflow.Workflow`.) When the prod axis should instead
  be ONE cached deliverable, make it a `RunAll...Prod` task that FANS OUT over the
  axis (`@oryxflow.requires_each`) - never a loop building a Workflow inside its
  `run()`, which puts the variants outside the DAG where no reset can reach them
  ([dynamic-dags.md](dynamic-dags.md)).
- **Selective reset by COST + AUTHORITY.** In `run_prod.py`, reset ONLY the
  cheap, fast-moving LOCAL source so a new period picks up fresh inputs; NEVER
  reset the expensive / external pulls - those are the frozen "trusted" baseline
  that must persist across prod runs. Scope it with
  `flow.reset_upstream(FinalTask, only=DataSource)`, which finds every instance of
  that family across the fan-out via the DAG, so adding a variant needs no edit
  here. (The ML case in [ml-patterns.md](ml-patterns.md) is the same principle with
  the model frozen and the data refreshed.)

A prod run that should itself be a CACHED, reproducible DAG node (aggregated
output saved, `code_version`-pinnable) stays a `RunAll...Prod` TASK; `run_prod.py`
is then just its thin entrypoint. Inline the orchestration in the run file only
for the simple case.

### Adding an app / reporting subsystem

An app (Streamlit, a report generator) goes at the project ROOT by default - the
same import / path-resolution reason notebooks do (cwd = project root, so
`from flow import flow` and relative `data/` paths resolve). Give it its own
`cfg_app.py` and a launch script. The app IMPORTS the flow, runs it, and reads
outputs via `flow.outputLoad(tasks.X)` - it NEVER reads `data/` directly (the
same trust-auto-file-management rule that governs everything else).

```python
# app-streamlit.py  (project root; launch: streamlit run app-streamlit.py)
import streamlit as st
import oryxflow
import cfg, cfg_app
import tasks
from flow_params import params_prod

params = {**params_prod, 'portfolio': st.session_state.portfolio}
flow = oryxflow.Workflow(tasks.Screen, params=params)
flow.run()
df = flow.outputLoad(tasks.Screen)   # load outputs; never read data/ directly
```

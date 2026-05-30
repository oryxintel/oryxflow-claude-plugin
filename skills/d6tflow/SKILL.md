---
name: d6tflow
description: >-
  Build and work with d6tflow data-science pipelines (Luigi-based: tasks,
  dependencies, parameters, caching, reproducible workflows). Use when working
  in a d6tflow project - the tasks.py / flow.py / run.py / cfg.py /
  flow_params.py files, pipeline tasks, workflow runs, or output analysis.
when_to_use: >-
  Trigger on requests like: create or modify a task, make one task depend on
  another, add or change a parameter, set the final task; run the flow, preview
  the flow (flow.preview), check what is cached, or re-run / reset a task; load
  or plot a task's output; explore or inspect the data (the opt-in deep dive);
  or summarize what the pipeline does.
argument-hint: "[explore]"
allowed-tools: Read Edit Write Grep Glob Bash
shell: powershell
---

# Working with d6tflow Data Science Projects

d6tflow is a Python library (built on Luigi) for reproducible, cacheable data
pipelines with automatic dependency management and incremental computation.

**Key Principle**: Follow the established project structure and file
organization. DO NOT create ad-hoc scripts or inline commands for workflow
operations - use the existing project files.

For the full library reference (task types, advanced patterns, data-science
recipes, debugging table, deep project-structure walkthrough), see
[reference.md](reference.md). For machine-learning pipelines (feature
engineering, model training, SHAP, expanding-window backtests), see
[ml-patterns.md](ml-patterns.md). Load either on demand when you need detail
beyond the essentials below.

---

## Session Start: Orient from Code + Data Doc, Don't Re-Scan

A d6tflow project documents itself in two places. Read these FIRST and trust
them - do NOT re-explore the whole project to rediscover what they already say:

- **The pipeline lives in the code.** `tasks.py` carries a module docstring (the
  workflow's goal/overview) and a docstring on each task (what it does); the DAG
  is the `@d6tflow.requires(...)` decorators (`flow.preview()` summarizes it for
  complex graphs); parameter meaning is commented where set in `flow_params.py`.
  There is NO separate pipeline doc - the code is the source of truth, so it
  cannot drift.
- **`docs/d6tflow-data.md`** - the data: sources, schema, quality issues,
  business rules, quirks. This is the one fact set with no code home (findings
  about external data, accumulated over time), so it lives in a file. A bigger
  project may split it into more `docs/d6tflow-data*.md` files (e.g. per source).

### The PLACEHOLDER marker tells you what is real

One uniform signal: a `PLACEHOLDER` marker means "not real yet - replace it, do
not trust it as a project fact."

- `tasks.py` / `flow_params.py` carry `# PLACEHOLDER SCAFFOLD` above the dummy
  logic (and the `tasks.py` module docstring is a placeholder until the real
  goal is written).
- `docs/d6tflow-data.md` carries a `PLACEHOLDER` comment on line 1.

No `PLACEHOLDER` markers left anywhere = a real, captured project.

### Default invocation is LIGHTWEIGHT - do not auto-explore

(The skill is invoked as `/d6tflow:d6tflow`; the bare `/d6tflow` and
`/d6tflow explore` written here and below are shorthand for that, with `explore`
passed as the argument. Most of the time it auto-activates and the user just
talks to it - no command needed.)

When the skill loads (e.g. plain `/d6tflow`) with no specific task, orient
cheaply and then STOP. Do the minimum:

1. Read the `tasks.py` module docstring + task docstrings, and
   `docs/d6tflow-data.md`. If the markers are gone, trust them.
2. If `tasks.py` still carries `PLACEHOLDER SCAFFOLD` -> fresh scaffold.
   Otherwise -> built pipeline (data doc maybe just not written yet).
3. Report the state in a sentence or two and ask what the user wants to do.
   For a built pipeline, summarize what it does. For a fresh scaffold, give the
   friendly onboarding orientation below instead of describing scaffold guts.

#### Fresh-scaffold orientation (do not narrate the placeholder logic)

The scaffold's placeholder internals - the dummy `DataFrame`, the example range,
the "doubles it" step - are throwaway wiring meant to be replaced. They are NOT
project facts, so do NOT report them ("GetData makes a dummy frame of range(10),
Process optionally doubles it"). That exposes internals the user does not care
about and reads as if the project does something it does not.

Instead, welcome the user and orient them toward getting started. Cover, briefly:

- This is a fresh d6tflow data-science project - the scaffold runs but does no
  real work yet.
- How to **create tasks**: define a task class in `tasks.py` (inherits a d6tflow
  task type, has a `run()` that ends in `self.save(...)`); wire dependencies with
  `@d6tflow.requires(...)`. (See "Add a new task" below.)
- How to **load data**: drop raw source files (`.csv`/`.xlsx`) into `data/` and
  read them in a `GetData`-style task; downstream tasks read upstream output with
  `self.inputLoad()`.
- How to **run the flow**: `python run.py` (it runs the final task set in
  `flow.py`); preview first with `flow.preview()`.

You can mention they can drive all of this in plain language - e.g. "create a
task `<Name>` that does ...", "make `<Task>` depend on `<Other>`", "run the
flow", "preview the flow", "re-run `<Task>`", "load the output of `<Task>`", or
"explore the data". Keep this to a couple of examples, not a full catalog.

Then offer the two natural next steps and ask which they want:
- `/d6tflow explore` - if they already have source data in `data/` to inspect.
- Describe the analysis goal + inputs, and you will replace the scaffold with
  real tasks.

Keep it short and inviting - a few lines plus the offer, not a tutorial dump.

Do NOT, on a plain invocation: list/inspect `data/`, read raw source files,
write or run `eda/` scripts, or build the docs. That is expensive exploration
and it is the USER's call to start it - see "Deep exploration is opt-in" below.

When the user DOES give a concrete task: if the code is documented (docstrings)
and the data doc is filled, trust them and open only the files that task touches.
Don't broadly re-scan to re-derive what they already describe.

The docstrings and the data doc are where the project writes down what it knows -
keep them accurate and the per-session re-scan disappears.

Document pipeline meaning IN THE CODE: a module docstring at the top of `tasks.py`
for the workflow goal, a docstring on each task for what it does. Capture data
findings in `docs/d6tflow-data.md`, deleting its `PLACEHOLDER` marker once filled.
Do not leave a marker on something you have actually filled.

### Deep exploration is opt-in

Full orientation - inspecting source data, profiling schema, and writing the
docs - runs ONLY when the user asks for it: `/d6tflow explore`, or a plain-
language request to "orient", "explore", "inspect the data", or "scan the
project". Until then, don't.

When explore IS requested:

- **Raw source data lives in `data/`** - typically loose files directly under it
  (`.csv`, `.xlsx`, etc.). Start there. Distinguish from task OUTPUT: d6tflow
  writes outputs into per-task subfolders as parquet (`data/GetData/*.parquet`,
  `data/Process/*.parquet`) - those are generated, not inputs, so ignore them
  when hunting for source data. The source path may point elsewhere via `cfg.py`;
  check it if `data/` has no raw files.
- Inspect schema with an `eda/` script (per the no-inline-Python rule), not ad
  hoc commands.
- Capture what you learn: data findings into `docs/d6tflow-data.md` (fill the
  scaffolded skeleton, removing the `PLACEHOLDER` marker); pipeline meaning as
  docstrings in `tasks.py` (module docstring for the goal, a docstring per task).
  This write-up is the payoff of exploring - don't skip it.

### Recognizing a fresh scaffold (the PLACEHOLDER marker)

Scaffold `.py` files are NOT blank - they ship runnable wiring so `python run.py`
works out of the box and the `from flow import flow` pattern is visible. The
placeholder logic (not the imports, which are real) carries a marker comment
directly above it so it cannot be mistaken for real work:
`# PLACEHOLDER SCAFFOLD - ...`

Use this marker to orient cheaply:

- **Wiring files** (`flow.py`, `run.py`, `cfg.py`) - real, identical-across-
  projects convention. Nothing to investigate; don't treat as project logic.
- **Content files** (`tasks.py`, `flow_params.py`) - if they still carry the
  `PLACEHOLDER SCAFFOLD` marker, nothing project-specific has been built yet.
  That marker IS the "fresh scaffold" signal - you do not need to read and judge
  the logic to decide. Your job is to REPLACE the marked block, not extend it.
- **Data doc** (`docs/d6tflow-data.md`) - same rule: a `PLACEHOLDER` marker on
  line 1 means not captured yet. Filling it means writing real facts and deleting
  that marker line.

When you build the real pipeline, delete the `PLACEHOLDER SCAFFOLD` lines along
with the dummy logic, write a real `tasks.py` module docstring + task docstrings,
and fill the data doc (removing its marker). A project with no `PLACEHOLDER`
markers left anywhere is a real, captured project.

---

## Core Concepts (essentials)

1. **Tasks** - Classes with a `run()` method that inherit a d6tflow task type
   (e.g. `TaskPqPandas`, `TaskPickle`). They save outputs automatically via
   `self.save()`. Identified by class name + parameters.
2. **Dependencies** - Declared with the `@d6tflow.requires()` decorator;
   d6tflow runs tasks in the correct order. Load upstream data with
   `self.inputLoad()`.
3. **Parameters** - Make tasks dynamic and reusable. They affect task identity
   (caching) and auto-inherit to downstream tasks. Use `significant=False` for
   params that should not affect identity.
4. **Workflows** - Created via `d6tflow.Workflow(FinalTask, params=params)`.
   A single workflow instance is imported everywhere: `from flow import flow`.
   Caching prevents re-running completed tasks.
5. **Project-structure pattern** - Separation of concerns across config, task
   definition, execution, and analysis layers (see below).

---

## Project File Organization

```
project/
|-- tasks.py           # Workflow task definitions (GetData -> Process)
|-- cfg.py             # Global configuration and settings
|-- flow_params.py     # Workflow-specific parameters
|-- flow.py            # Workflow instance definition
|-- run.py             # Execute workflow tasks
|-- visualize.py       # Analysis script
|-- visualize.ipynb    # Analysis notebook
|-- .creds.yaml        # Protected credentials (optional, not committed)
|-- data/              # Data storage (task outputs + raw/exported data)
|-- docs/              # Project documentation
|-- reports/           # Output reports and plots (version controlled)
`-- reports/render/    # Temporary report output (not version controlled)
```

**Central Pattern**: `from flow import flow`  # Import everywhere

File flow: `cfg.py` -> `flow_params.py` -> `tasks.py` -> `flow.py` ->
`run.py` / `visualize.py` / `visualize.ipynb` (all import the same `flow`).

---

## Workflow Operations: Use Existing Files

DO NOT create ad-hoc Python scripts or inline bash commands.

NEVER do this:
```bash
python -c "import d6tflow; flow = d6tflow.Workflow(...); flow.run()"
```

ALWAYS do this:

- **Modify workflow logic** - Edit `tasks.py` (task classes),
  `flow_params.py` (parameters), or `flow.py` (which final task runs).
- **Run the workflow** - Edit `run.py` if needed (e.g. uncomment reset calls),
  then run `python run.py`.
- **Analyze outputs** - Edit `visualize.py` then run `python visualize.py`,
  or use `visualize.ipynb` interactively.

NEVER write inline Python (no `python -c`, no inline snippets). ALL test / EDA /
exploratory code goes in a file under `eda/{meaningful-file-name}.py` and is
then executed (`python eda/{name}.py`). Give the file a descriptive name for the
exploration it performs.

### Python REPL / script commands
```python
from flow import flow
import tasks

flow.preview()                    # Preview what will run
flow.run()                        # Run workflow
flow.complete()                   # Check if complete (True/False)
flow.reset(tasks.TaskName)        # Force re-run from task
df = flow.outputLoad(tasks.Task)  # Load task output
```

**Trust auto file management**: if `flow.run()` completes without errors, the
output files exist. Debug by loading with `flow.outputLoad()`, NOT by checking
the file system.

---

## Code Style: ASCII Only

DO NOT use Unicode symbols (emojis, checkmarks, special characters) in code or
print statements - they cause encoding issues on Windows.

NEVER:
```python
print("Success!")   # with a checkmark/emoji prefix
```
ALWAYS:
```python
print("SUCCESS: Operation completed")
print("WARNING: Issue detected")
print("ERROR: Operation failed")
```

### No try/except wrapping

DO NOT wrap code in try/except blocks. Let it fail natively so errors surface.
Exceptions (only): when the user expressly asks for it, or in temporary / EDA
code under `eda/`.

### Assume given file paths exist

When the user provides a file path, assume it exists - do NOT add existence
checks (`os.path.exists`, etc.) before reading it. If it does not exist, the
read will raise an error, which is the desired behavior.

---

## Reading Locked Excel Files

When loading an Excel file that is currently open and locked (read fails with a
permission/sharing error), DO NOT work around it (e.g. copying to a temp file).
Instead, STOP and ask the user to close the file, then retry the read.

---

## Common Workflow Patterns

### Add a new task
1. Define the task in `tasks.py`:
```python
@d6tflow.requires(UpstreamTask)
class NewTask(d6tflow.tasks.TaskPqPandas):
    """Brief description of what this task does"""
    param1 = d6tflow.Parameter()

    def run(self):
        df = self.inputLoad()
        # process data
        self.save(df_processed)
```
2. Add parameters to `flow_params.py`: `params['param1'] = 'value'` (comment what
   the parameter means there).
3. If it is the new final task, set `task = tasks.NewTask` in `flow.py`.
4. Give the task a clear docstring (that IS its documentation); update the
   `tasks.py` module docstring if the workflow's goal changed.

### Modify an existing task
1. Edit the task in `tasks.py`.
2. Force re-run: uncomment `flow.reset(tasks.ModifiedTask)` in `run.py`.
3. Run `python run.py`.
4. Keep the task's docstring accurate.

### Change parameters
1. Edit `flow_params.py`: `params['param'] = 'new_value'`.
2. Run `python run.py` (the change is auto-detected).
3. Update the parameter's comment in `flow_params.py` if its meaning changed.

### Debug workflow issues
```python
flow.preview()                         # Preview what will run
flow.complete()                        # Check completion
df = flow.outputLoad(tasks.Task)       # Inspect outputs
flow.reset(tasks.Task); flow.run()     # Force re-run
```

---

## Quick Reference

**Task types**: `TaskPqPandas` (DataFrames as Parquet, FASTEST - default),
`TaskPickle` (any Python object: models, dicts, lists), `TaskJson`
(dicts / simple structures). Full table in [reference.md](reference.md).

**Loading**: `df = self.inputLoad()` (single), `df1, df2 = self.inputLoad()`
(multiple), `meta = self.metaLoad()` (metadata).

**Saving**: `self.save(df)` (single), `self.save([df1, df2], from_list=True)`
(multiple), `self.saveMeta({'model': model})` (models/configs).

---

## Project Documentation to Maintain

This is what a future session reads at "Session Start" above to skip
re-scanning, so update it as part of the same change, not later. Document in code
by default; use a file only for what has no code home:

- **Pipeline -> in the code.** Per-task meaning is the task docstring; the
  workflow goal/overview is the `tasks.py` module docstring; parameter meaning is
  a comment where set in `flow_params.py`; structure is the
  `@d6tflow.requires(...)` decorators (`flow.preview()` summarizes it). Do NOT
  keep a separate pipeline doc - it would only duplicate the code and drift.
- **`docs/d6tflow-data.md`** - data findings: sources, schema, quality issues,
  business rules, quirks. This has no code home (findings about external data,
  accumulated over time), so it lives in a file. Update when you discover schema
  details or data issues.

If you finish a change without updating these, the next session pays the scan
cost you just avoided. Treat it as part of "done."

A project scaffolded with `/d6tflow:project-init` ships `docs/d6tflow-data.md` as
a short `PLACEHOLDER` skeleton; fill it in place and delete the marker line. If it
is absent, recreate it with the headings: sources / schema / quality issues /
business rules / open questions.

---

## Additional Resources

- [reference.md](reference.md) - comprehensive d6tflow patterns and reference.
- [ml-patterns.md](ml-patterns.md) - ML pipeline task templates (features,
  training, SHAP, expanding-window backtest). Load on demand for ML work.
- d6tflow docs: https://d6tflow.readthedocs.io/
- d6tflow GitHub: https://github.com/d6t/d6tflow

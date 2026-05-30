---
name: d6tflow
description: >-
  Build highly effective data science workflows with d6tflow (parameterized
  tasks, dependencies, caching, reproducible pipelines). Use when working in a
  d6tflow project - the tasks.py / flow.py / run.py / cfg.py / flow_params.py
  files, pipeline tasks, workflow runs, or output analysis.
when_to_use: >-
  Trigger on requests like: add a new task that depends on an existing one
  (wired with @d6tflow.requires), create a task that loads a source, add a task
  with multiple inputs, update / modify an existing task, make one task depend on
  another, set the final task, or add / change a parameter; run the flow, preview
  it (flow.preview), check what is cached, or re-run / reset a task (reset before
  re-running an edited task); load or plot a task's output; explore or inspect
  the data (the opt-in deep dive); or summarize what the pipeline does.
argument-hint: "[explore]"
allowed-tools: Read Edit Write Grep Glob Bash
shell: powershell
---

# Working with d6tflow Data Science Projects

d6tflow is a Python library for building highly effective data science
workflows. It lets you chain together complex, parameterized data flows and
execute them, caching intermediate results and rerunning intelligently after
code or parameter changes - so you build better models faster.

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
  read them in a data-loading task named for what it produces (e.g. `DataOEWS`,
  not `GetData` - see "Naming tasks"); downstream tasks read upstream output with
  `self.inputLoad()`.
- How to **run the flow**: `python run.py` (it runs the final task set in
  `flow.py`); preview first with `flow.preview()`.

You can mention they can drive all of this in plain language - e.g. "add a task
`<Name>` that takes `<Upstream>`'s output and ..." (a new task wired with
`@d6tflow.requires`), "run the flow", "load the output of `<Task>`", or "explore
the data". Keep this to a couple of examples, not a full catalog.

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
for the workflow goal, and a real docstring on each task (see "Task docstrings" -
intent + input/output contract, not restated code). Capture data findings in
`docs/d6tflow-data.md`, deleting its `PLACEHOLDER` marker once filled. Do not
leave a marker on something you have actually filled.

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
with the dummy logic, write real tasks named for their output (see "Naming
tasks" - replace `GetData` / `Process`, do not write into them), add a real
`tasks.py` module docstring + task docstrings, and fill the data doc (removing
its marker). A project with no `PLACEHOLDER` markers left anywhere is a real,
captured project.

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
  then run `python run.py`. If a task's CODE was just edited, reset it first
  (`flow.reset(tasks.X)`) - a plain run skips edited-but-unreset tasks. See
  "Modify an existing task".
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

### Naming tasks (name for the OUTPUT, not the verb)

A task's name should describe the output it produces, not the action it performs.
The output is what downstream code and the cache are keyed on, so the name reads
as a noun: `OEWSWages`, `CleanedSales`, `FeatureMatrix`, `TrainedModel`. For a
task whose job is to load/produce a named dataset, `Data<Name>` is a fine pattern
(`DataOEWS`); a plain `<Name>` describing the output (`OEWS`) is equally good.
Avoid generic verb names like `GetData`, `LoadData`, `Process`, `Run` - they say
nothing about what comes out and collide across projects.

A plain-language request to "load the OEWS data" (or "load X", "get X", "pull X")
IS a request to create such a task - create a NEW, output-named task for it
(e.g. `DataOEWS`); do not load the data inline or outside the task structure.

The scaffold's `GetData` / `Process` are PLACEHOLDER names. Building the real
pipeline means writing new, output-named tasks and deleting the placeholders -
NOT renaming-in-place or writing your real logic into `GetData`. Never extend
`GetData` / `Process`; replace them.

### Task docstrings (they ARE the docs)

Pipeline documentation lives in the code, so a task's docstring is its
documentation - write it properly, not as a throwaway "brief description". State:

- what the task PRODUCES (one line: the purpose / output);
- its input -> output contract (what it consumes and from where; what columns /
  keys it saves - this is what downstream tasks and readers depend on);
- any non-obvious decision, assumption, or quirk (point to
  `docs/d6tflow-data.md` for data-specific ones).

Do NOT restate the code. The docstring explains intent and contract; the body
shows how. Include a short snippet only when it is the clearest way to state a
contract (e.g. an output column list) - never a copy of the run() logic. Same
rule for the `tasks.py` module docstring (the workflow goal) and the data doc:
describe and decide, do not paste code.

### Add a new task
1. Define the task in `tasks.py`, named for its output (see "Naming tasks") with
   a docstring that IS its documentation (see "Task docstrings"):
```python
@d6tflow.requires(DataOEWS)
class OEWSWages(d6tflow.tasks.TaskPqPandas):
    """Median hourly and annual wage per occupation x metro area.

    In:  OEWS MSA estimates (from DataOEWS).
    Out: one row per (occ_code, area); the wage-percentile columns. Null where
         BLS suppressed small cells - see docs/d6tflow-data.md.
    """
    param1 = d6tflow.Parameter()

    def run(self):
        df = self.inputLoad()
        # ... transform ...
        self.save(df_out)
```
2. Add parameters to `flow_params.py`: `params['param1'] = 'value'` (comment what
   the parameter means there).
3. If it is the new final task, set `task = tasks.OEWSWages` in `flow.py`.
4. The docstring is the task's documentation - keep it accurate. Update the
   `tasks.py` module docstring if the workflow's goal changed.

### Modify an existing task (the common iterate loop)
1. Edit the task's `run()` in `tasks.py`.
2. RESET IT BEFORE RUNNING. A code edit does NOT change the task's identity
   (class + parameters), so d6tflow still considers it complete and a plain
   `python run.py` will SKIP it and reuse the stale cached output. Reset the task
   first: `flow.reset(tasks.ModifiedTask)`. Reset cascades downstream, so the one
   reset also forces the tasks that depend on it to recompute.
3. Run: add/uncomment `flow.reset(tasks.ModifiedTask)` in `run.py`, run
   `python run.py`, then re-comment the reset line.
4. Keep the task's docstring accurate.

**Iterate-then-run rule**: if a task's code was edited this session (by you or
the user) and you are then asked to "run the flow", do reset-then-run for that
task - do NOT just `python run.py`, or the edit silently does nothing.

### Change parameters
1. Edit `flow_params.py`: `params['param'] = 'new_value'`.
2. Run `python run.py`. A parameter change IS auto-detected (it changes task
   identity), so no reset is needed - unlike a code edit.
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

---
name: d6tflow
description: >-
  Build highly effective data science workflows with d6tflow (parameterized
  tasks, dependencies, caching, reproducible pipelines). Use when working in a
  d6tflow project - the tasks.py / flow.py / run.py / cfg.py / flow_params.py
  files, pipeline tasks, workflow runs, output analysis, or publishing/rendering
  a report notebook to HTML.
when_to_use: >-
  Trigger on requests like: add a new task that depends on an existing one
  (wired with @d6tflow.requires), create a task that loads a source, add a task
  with multiple inputs, update / modify an existing task, make one task depend on
  another, set the final task, or add / change a parameter; run the flow, preview
  it (flow.preview), check what is cached, or re-run / reset a task (reset before
  re-running an edited task); load or plot a task's output; explore or inspect
  the data (the opt-in deep dive); summarize what the pipeline does; or
  publish / render / export a report notebook to HTML (jupyter nbconvert), or
  re-execute a notebook to refresh its outputs.
argument-hint: "[explore]"
allowed-tools: Read Edit Write Grep Glob Bash
shell: powershell
---

# Working with d6tflow Data Science Projects

d6tflow is a Python library for building highly effective data science
workflows: chain complex, parameterized data flows and execute them, caching
intermediate results and rerunning intelligently after code or parameter changes
- so you build better models faster.

**Key Principle**: Follow the established project structure. DO NOT create
ad-hoc scripts or inline commands for workflow operations - use the existing
project files.

Depth lives on demand, not here: [reference.md](reference.md) for the full
library reference (task types, advanced patterns, recipes, debugging, deep
project-structure walkthrough); [ml-patterns.md](ml-patterns.md) for ML pipeline
templates (features, training, SHAP, expanding-window backtests). Load either
when you need more than the essentials below.

---

## Session Start: Orient from Code + Data Doc, Don't Re-Scan

A d6tflow project documents itself in two places. Read these FIRST and trust
them - do NOT re-explore the whole project to rediscover what they say. Keeping
them current is part of "done" for every change; skip it and the next session
pays the scan cost again.

- **Pipeline meaning -> in the code.** `tasks.py` has a module docstring (the
  workflow goal) and a docstring per task; the DAG is the `@d6tflow.requires(...)`
  decorators (`flow.preview()` summarizes complex graphs); parameter meaning is
  commented in `flow_params.py`. There is NO separate pipeline doc - the code is
  the source of truth, so it cannot drift. Write it well: see "Task docstrings".
- **Data findings -> `docs/d6tflow-data.md`.** Sources, schema, quality issues,
  business rules, quirks - the one fact set with no code home. A big project may
  split it into more `docs/d6tflow-data*.md` files. If absent, recreate it with
  headings: sources / schema / quality issues / business rules / open questions.

### The PLACEHOLDER marker tells you what is real

One signal across code AND docs: a `PLACEHOLDER` marker means "not real yet -
replace it, do not trust it, do not extend it." No markers left anywhere = a
real, captured project. When you build the real pipeline, delete the markers
along with the dummy logic.

- **Wiring** (`flow.py`, `run.py`, `cfg.py`) - real, identical across projects.
  Not project logic; nothing to investigate.
- **Content** (`tasks.py`, `flow_params.py`) - a `# PLACEHOLDER SCAFFOLD` comment
  above the dummy logic (and a placeholder module docstring) means nothing
  project-specific is built. REPLACE the marked block; don't read it to decide.
- **Data doc** (`docs/d6tflow-data.md`) - a `PLACEHOLDER` on line 1 = not
  captured yet.

### Default invocation is LIGHTWEIGHT - do not auto-explore

(Invoked as `/d6tflow:d6tflow`; bare `/d6tflow` and `/d6tflow explore` are
shorthand. Usually it auto-activates and the user just talks to it.)

On a plain load with no specific task, orient cheaply and STOP:

1. Read the `tasks.py` docstrings and `docs/d6tflow-data.md`. If markers are
   gone, trust them.
2. `tasks.py` still carries `PLACEHOLDER SCAFFOLD` -> fresh scaffold; else ->
   built pipeline (data doc maybe just not written yet).
3. Report the state in a sentence or two and ask what the user wants. Built
   pipeline: summarize what it does. Fresh scaffold: give the onboarding below
   (do NOT describe scaffold guts). Either way, END with example invocations.

Do NOT, on a plain invocation: list/inspect `data/`, read raw sources, write or
run `eda/` scripts, or build the docs - that is opt-in exploration (below).

When the user gives a concrete task: trust the docstrings + data doc and open
only the files that task touches; don't re-scan to re-derive what they describe.

#### Example invocations to offer

In-session is where the user discovers how to drive the skill (README isn't
visible mid-session; `argument-hint` only shows `[explore]`). After orienting,
show a short, GROUPED set - pick a handful that fit the state, don't dump all:

- Build: "load the `<X>` data" (creates an output-named loader task), "add a task
  `<Name>` that takes `<Upstream>`'s output and ...", "make `<A>` depend on
  `<B>`", "set `<Task>` as the final task", "add a parameter `<name>`".
- Run: "run the flow", "preview the flow", "re-run / reset `<Task>`".
- Inspect: "load the output of `<Task>`", "plot the results".
- Understand: "what does this pipeline do?", "explore the data".

Tell the user they can ask "what can I do here?" anytime (the README's "Things
you can ask" is the fuller version). Same list answers "how do I use this" /
"help".

#### Fresh-scaffold orientation

The scaffold's placeholder internals (dummy `DataFrame`, example range, the
"doubles it" step) are throwaway wiring, NOT project facts - do NOT narrate them
(it reads as if the project does real work). Instead, welcome and orient briefly:

- This is a fresh d6tflow project - the scaffold runs but does no real work yet.
- **Create tasks**: a task class in `tasks.py` (inherits a d6tflow task type,
  `run()` ends in `self.save(...)`); wire deps with `@d6tflow.requires(...)`.
  (See "Add a new task".)
- **Load data**: drop raw files (`.csv`/`.xlsx`) into `data/` and read them in a
  task named for what it produces (`DataOEWS`, not `GetData` - see "Naming
  tasks"); downstream tasks read upstream output via `self.inputLoad()`.
- **Run the flow**: `python run.py` (runs the final task set in `flow.py`);
  preview first with `flow.preview()`.

Surface the example invocations, then offer the two next steps and ask which:
`/d6tflow explore` (if source data already in `data/`), or describe the goal +
inputs and you replace the scaffold with real tasks. Keep it short and inviting.

### Deep exploration is opt-in

Inspecting source data, profiling schema, and writing the docs run ONLY when the
user asks: `/d6tflow explore`, or a plain-language "orient" / "explore" /
"inspect the data" / "scan the project". Until then, don't. When requested:

- **Raw source data lives in `data/`** - loose files directly under it (`.csv`,
  `.xlsx`, ...). Distinguish from task OUTPUT: d6tflow writes outputs as parquet
  into per-task subfolders (`data/GetData/*.parquet`) - generated, not inputs, so
  ignore them. The source path may point elsewhere via `cfg.py`.
- Inspect schema with an `eda/` script (no-inline-Python rule), not ad hoc.
- Capture what you learn - the payoff: data findings into `docs/d6tflow-data.md`
  (remove its `PLACEHOLDER`); pipeline meaning as `tasks.py` docstrings.

---

## Core Concepts (essentials)

1. **Tasks** - Classes with a `run()` method that inherit a d6tflow task type
   (`TaskPqPandas`, `TaskPickle`, ...). They save outputs via `self.save()`.
   Identified by class name + parameters.
2. **Dependencies** - Declared with `@d6tflow.requires()`; d6tflow runs tasks in
   order. Load upstream data with `self.inputLoad()`.
3. **Parameters** - Make tasks dynamic and reusable. They affect task identity
   (caching) and auto-inherit downstream. Use `significant=False` for params that
   should not affect identity.
4. **Workflows** - `d6tflow.Workflow(FinalTask, params=params)`. One instance is
   imported everywhere (`from flow import flow`). Caching skips completed tasks.
5. **Project-structure pattern** - Separation of concerns across config, task
   definition, execution, and analysis layers (below).

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
|-- visualize.ipynb    # Analysis notebook (importing notebooks stay at root)
|-- .creds.yaml        # Protected credentials (optional, not committed)
|-- eda/               # Test / exploration probes, grouped by subject
|-- utils/             # Shared + per-subject helpers (snake_case modules)
|-- viz/               # Plotting helpers + per-subject figures
|-- data/              # Data storage (task outputs + raw/exported data)
|-- docs/              # Project documentation
|-- reports/           # Output reports and plots (version controlled)
`-- reports/render/    # Temporary report output (not version controlled)
```

**Central pattern**: `from flow import flow`  # import everywhere.
File flow: `cfg.py` -> `flow_params.py` -> `tasks.py` -> `flow.py` ->
`run.py` / `visualize.py` / `visualize.ipynb` (all import the same `flow`).

**Code organization** (full rules + edge cases in reference.md): group supporting
code by SUBJECT - a task, dataset, or concept, snake_case: `eda/<subject>/<name>.py`
(READ-ONLY probes), `utils/<subject>.py`, `viz/<subject>.py`. A helper shared by
2+ subjects goes in a concept/dataset module (`utils/geo.py`); a single subject's
helper in `utils/<subject>.py`; only truly generic helpers in `__init__.py`. Name
files for the specific thing they do, dropping the redundant subject token
(`eda/data_oews/verify_coercion.py`) - never a bare verb. Loading external data is a
SOURCE TASK by default (the loader-task pattern), not an `eda/` probe - unless it
is hand-curated, or its output is not a table/serializable object a task stores,
which stays a maintenance script.

---

## Workflow Operations: Use Existing Files

DO NOT create ad-hoc Python scripts or inline bash commands.

NEVER: `python -c "import d6tflow; flow = d6tflow.Workflow(...); flow.run()"`

ALWAYS:

- **Modify logic** - Edit `tasks.py` (task classes), `flow_params.py`
  (parameters), or `flow.py` (which final task runs).
- **Run** - Edit `run.py` if needed, then `python run.py`. If a task's CODE was
  just edited, reset it first (`flow.reset(tasks.X)`) - a plain run skips
  edited-but-unreset tasks. Keep `flow.reset(...)` lines in `run.py` as
  commented-out toggles (uncomment to reset, re-comment after); don't delete
  them. See "Modify an existing task".
- **Analyze outputs** - Edit `visualize.py` then `python visualize.py`, or use
  `visualize.ipynb` interactively.
- **Publish a report** - Keep notebooks that import the flow at the project root
  (so imports + `data/` paths resolve); render them to `reports/render/`
  (gitignored). See "Render / publish a notebook" below.

**Run from the working directory.** The shell starts in the project root, so run
`python run.py` and `python visualize.py` directly - do NOT prepend
`cd <project path>` (redundant, and brittle when the path has spaces).

**EDA scripts import project modules** (`from flow import flow`), so run them as a
MODULE from the root: `python -m eda.<subject>.<name>` (dotted path, no `.py`;
each `eda/<subject>/` needs an `__init__.py`). Running the file directly FAILS -
it puts the folder on `sys.path` instead of the root, so `import flow` /
`import tasks` break. Do NOT patch `sys.path`; use `python -m`.

**No inline Python** - no `python -c` or snippets, including quick one-off probes
("just checking X" is exactly what this forbids). ALL test / EDA code goes in an
`eda/<subject>/<name>.py` file (run as a module, above) - near-free to write,
re-runnable next session, and free of the Windows shell-quoting bugs `python -c`
hits.

**Document each probe** - the code is throwaway, the finding is not. One-line
docstring stating the question; print the result legibly. Promote material
findings (schema, quirks, quality, rules) to `docs/d6tflow-data.md` - an
uncaptured result is a question you re-ask next session.

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

### Render / publish a notebook

Notebooks that import the pipeline live at the PROJECT ROOT (like
`visualize.ipynb`), NOT in `reports/`. `nbconvert --execute` runs the kernel with
cwd = the notebook's own folder, so a notebook in a subdirectory breaks both
`from flow import flow` and the relative `data/` paths d6tflow reads/writes; at the
root, cwd = the project root and everything resolves. `reports/render/` holds the
rendered HTML (gitignored - regenerated output). Run nbconvert from the root.

Refresh a notebook's outputs in place first (re-executes every cell against
current data, saving results back into the `.ipynb`):
```bash
jupyter nbconvert --to notebook --execute --inplace <name>.ipynb
```
Then publish to a standalone HTML file:
```bash
jupyter nbconvert <name>.ipynb --to html --output-dir reports/render \
  --no-input --no-prompt --template classic
```
The three flags are REQUIRED, not optional polish - they are what makes it a
publishable report: `--no-input` and `--no-prompt` strip the code cells and
prompt numbers, and `--template classic` gives a clean layout. Without them you
publish the raw working notebook (code and all), which is not the goal. Do not
drop them. (`--output-dir` writes there directly; prefer it over `--output`,
whose path is relative to the input notebook.)

Re-execute whenever upstream data or task code changed, so the published report
does not show stale cell outputs.

---

## Code Style

**ASCII only.** No Unicode (emojis, checkmarks, special chars) in code or print
statements - they break encoding on Windows. Use plain prefixes:
```python
print("SUCCESS: Operation completed")
print("WARNING: Issue detected")
print("ERROR: Operation failed")
```

**No try/except wrapping.** Let code fail natively so errors surface. Exceptions
only: when the user asks, or in temporary / EDA code under `eda/`.

**Assume given file paths exist.** When the user provides a path, don't add
existence checks (`os.path.exists`) - a missing file should raise on read.

**Reading locked Excel files.** If an Excel read fails because the file is open
and locked (permission/sharing error), do NOT work around it (e.g. temp copy).
STOP and ask the user to close it, then retry.

---

## Common Workflow Patterns

### Naming tasks (name for the OUTPUT, not the verb)

Name a task for the output it produces, not the action - the output is what
downstream code and the cache are keyed on, so the name reads as a noun:
`OEWSWages`, `CleanedSales`, `FeatureMatrix`, `TrainedModel`. For a task that
loads/produces a named dataset, `Data<Name>` (`DataOEWS`) or a plain `<Name>`
(`OEWS`) are both fine. Avoid generic verbs (`GetData`, `LoadData`, `Process`,
`Run`) - they say nothing about the output and collide across projects.

A plain-language "load the OEWS data" (or "load/get/pull X") IS a request to
create such a task - make a NEW, output-named task (`DataOEWS`); don't load data
inline or outside the task structure. Before writing it, it is fine (not
required) to write throwaway EDA under `eda/` to figure out the source (sheets,
columns, parsing); otherwise just write the task and iterate by running it
(adjust `run()`, reset, re-run). The actual loading always lands in the task.

The scaffold's `GetData` / `Process` are PLACEHOLDER names: write new output-named
tasks and DELETE them - never rename-in-place or write real logic into them.

### Task docstrings (they ARE the docs)

Pipeline docs live in the code, so a task's docstring is its documentation - not
a throwaway "brief description". State:

- what the task PRODUCES (one line: purpose / output);
- its input -> output contract (what it consumes and from where; what columns /
  keys it saves - what downstream tasks depend on);
- any non-obvious decision/assumption/quirk (point to `docs/d6tflow-data.md` for
  data-specific ones).

Do NOT restate the code - explain intent and contract; the body shows how.
Include a short snippet only when it is the clearest way to state a contract
(e.g. an output column list). Same rule for the `tasks.py` module docstring and
the data doc.

### Add a new task
1. Define it in `tasks.py`, named for its output, with a real docstring:
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
   it means).
3. If it is the new final task, set `task = tasks.OEWSWages` in `flow.py`.
4. Keep the docstring accurate; update the module docstring if the goal changed.

### Modify an existing task (the common iterate loop)
1. Edit the task's `run()` in `tasks.py`.
2. RESET IT BEFORE RUNNING. A code edit does NOT change task identity (class +
   parameters), so d6tflow treats it as complete and a plain `python run.py`
   SKIPS it, reusing the stale output. `flow.reset(tasks.ModifiedTask)` first -
   reset cascades downstream, recomputing dependents too.
3. Run: add/uncomment `flow.reset(tasks.ModifiedTask)` in `run.py`, run
   `python run.py`, then re-comment the reset line. Keep reset calls as
   commented-out toggles in `run.py` (one task per line; uncomment several at
   once to reset multiple) rather than deleting them - the standing list of
   reset-ables is the intended pattern.
4. Keep the docstring accurate.

**Iterate-then-run rule**: if a task's code was edited this session and you are
then asked to "run the flow", do reset-then-run for that task - do NOT just
`python run.py`, or the edit silently does nothing.

**Across parameter variants**: a code edit invalidates EVERY cached instance of
that task (one per parameter value), but `flow.reset(...)` / the run only
recompute the variant(s) you actually run. If you edited `EmploymentExposure`'s
columns and ran it for `jobs='customer_service'`, the `support_broad` /
`backoffice` outputs are STILL stale - loading one later yields the old schema
(e.g. `KeyError: 'jobs_pct_AIadj'`). When iterating over variants, force a
recompute per setting with `reset=True`:
```python
# code changed -> reset=True recomputes this variant instead of loading stale cache
df = d6tflow.runLoad(tasks.EmploymentExposure, params={'jobs': jobs}, reset=True)
```

### Change parameters
1. Edit `flow_params.py`: `params['param'] = 'new_value'`.
2. Run `python run.py`. A parameter change IS auto-detected (it changes identity)
   - no reset needed, unlike a code edit.
3. Update the parameter's comment if its meaning changed.

For settings you switch between or compare often, keep the alternatives as
commented-out lines and toggle by commenting/uncommenting rather than rewriting
the value - the standing list documents the available options:
```python
# params['model'] = 'baseline'        # alternatives, uncomment to switch
params['model'] = 'gradient_boost'

# params['window'] = 30
params['window'] = 90
```

### Debug workflow issues
```python
flow.preview()                         # Preview what will run
flow.complete()                        # Check completion
df = flow.outputLoad(tasks.Task)       # Inspect outputs
flow.reset(tasks.Task); flow.run()     # Force re-run
```

**Read the Execution Summary to see what ACTUALLY ran.** After a run, the summary
distinguishes recomputed tasks from cache hits - use it to confirm your reset
took effect (not just that the run succeeded):
```
* 2 complete ones were encountered:   <- loaded from cache, did NOT re-run
    - 1 EmploymentbyMSA(jobs=support_broad)
* 1 ran successfully:                  <- actually recomputed
    - 1 EmploymentExposure(jobs=support_broad)
```
If a task you edited shows under "complete ones were encountered" instead of "ran
successfully", it was skipped (stale cache) - reset it and re-run.

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

## Additional Resources

- [reference.md](reference.md) - comprehensive d6tflow patterns and reference.
- [ml-patterns.md](ml-patterns.md) - ML pipeline task templates. Load on demand.
- d6tflow docs: https://d6tflow.readthedocs.io/ | GitHub: https://github.com/d6t/d6tflow

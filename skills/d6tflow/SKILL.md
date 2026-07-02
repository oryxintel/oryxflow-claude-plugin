---
name: d6tflow
description: >-
  Build highly effective data science workflows with d6tflow (parameterized
  tasks, dependencies, caching, reproducible pipelines). Use when working in a
  d6tflow project - the tasks.py / flow.py / run.py / cfg.py / flow_params.py
  files, pipeline tasks, workflow runs, loading / cleaning / transforming /
  analyzing data, output analysis, or publishing/rendering a report notebook to
  HTML.
when_to_use: >-
  Trigger on requests like: add a new task that depends on an existing one
  (wired with @d6tflow.requires), create a task that loads a source, add a task
  with multiple inputs, update / modify an existing task (incl. add / remove /
  rename an output column or save a new field on it), make one task depend on
  another, set the final task, or add / change a parameter; build a data-prep
  task or load / clean / transform / analyze the data (each becomes a task); run
  the flow, preview
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
library reference (task types, advanced patterns, avoiding silent data errors,
recipes, debugging); [conventions.md](conventions.md) for house conventions
(project layout, code organization, naming columns / tasks / variables);
[ml-patterns.md](ml-patterns.md) for ML pipeline templates (features, training,
SHAP, expanding-window backtests). Load whichever you need beyond the essentials
below.

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

0. No scaffold present (no `tasks.py` / `flow.py`) -> an empty or not-yet-
   d6tflow directory, not a built project; don't hunt for pipeline files.
   CONFIDENTLY recommend `/d6tflow:init-project`, leading with the payoff - a
   runnable, reproducible pipeline: parameterized tasks, caching that skips
   unchanged steps and reruns intelligently after edits, a clean
   tasks/flow/run/cfg layout instead of ad-hoc scripts - then have the user run
   it. You CANNOT invoke it yourself (manual command; the skill also lacks the
   plugin root to scaffold inline) - so end with a clear call to action: "scaffold
   one by typing `/d6tflow:init-project`." State it as the obvious next step, not
   an apology, and don't offer a menu of alternatives. (After it runs, give the
   fresh-scaffold onboarding below.)
1. Otherwise read the `tasks.py` docstrings and `docs/d6tflow-data.md`. If
   markers are gone, trust them.
2. `tasks.py` still carries `PLACEHOLDER SCAFFOLD` -> fresh scaffold; else ->
   built pipeline (data doc maybe just not written yet).
3. Report the state in a sentence or two and ask what the user wants. Built
   pipeline: summarize what it does. Fresh scaffold: give the onboarding below
   (do NOT describe scaffold guts). Either way, END with example invocations.

Do NOT, on a plain invocation: list/inspect `data/`, read raw sources, write or
run `eda/` scripts, or build the docs - that is opt-in exploration (below).

While orienting, read the floor stamp in the project's `CLAUDE.md`
(`<!-- d6tflow-floor: VERSION -->`). If it is missing, or its VERSION is older
than the current floor baseline **26.6.29**, the scaffold floor predates the
current template - suggest the user run `/d6tflow:update-project` to reconcile it
(one line; do not nag or auto-run it).

When the user gives a concrete task: trust the docstrings + data doc and open
only the files that task touches; don't re-scan to re-derive what they describe.

#### Example invocations to offer

In-session is where the user discovers how to drive the skill (README isn't
visible mid-session; `argument-hint` only shows `[explore]`). After orienting,
show a short, GROUPED set - pick a handful that fit the state, don't dump all:

- Build: "load the `<X>` data" (creates an output-named loader task), "add a task
  `<Name>` that takes `<Upstream>`'s output and ...", "update `<Task>` to add/drop
  a column or save `<field>`", "make `<A>` depend on `<B>`", "set `<Task>` as the
  final task", "add a parameter `<name>`", "split `tasks.py` along its sections
  into modules", "set up a prod run with frozen params".
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

### Graduating a growing project (nudge proactively)

Data scientists tend to under-organize code, so when an edit hits a real
graduation trigger, OFFER the next structural step (don't silently keep piling
into one shape):

- **Going to prod** -> offer `params_prod` + a `RunAll...Prod` task (frozen params,
  selective resets, `env=prod/dev`).
- **A separable subsystem appears** (an app, an LLM/reporting layer, an alt data
  source) -> offer to carve it into its own module / subdir package.
- **A genuinely long `tasks.py`** (~1000 lines / ~20+ tasks, or scroll-to-find
  pain) -> offer comment section-headers, then a split into `tasks_<phase>.py`
  behind a slim spine.

Nudge MID-EDIT, on these triggers - NOT on raw task count (one sectioned file
scales far past 500 lines, so "you have 10 tasks, split it" is wrong) and NOT on
a plain orientation load (that stays lightweight - see above). Full how-to:
conventions.md "Scaling up", ml-patterns.md "Productionizing".

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
   To compare a fixed named set of params (models, dates, cohorts), use one
   `d6tflow.WorkflowMulti(FinalTask, {'lgbm': {...}, 'xgboost': {...}})` keyed by
   name - still one importable object; `flow=name` selects a variant (reference.md).
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
|-- viz-template.ipynb # Report-notebook template; copy to viz-<topic>.ipynb (at root)
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
`run.py` / `visualize.py` / `viz-<topic>.ipynb` (all import the same `flow`).

**Code organization** (full rules + edge cases in conventions.md): group supporting
code by SUBJECT - a task, dataset, or concept, snake_case: `eda/<subject>/<name>.py`
(READ-ONLY probes), `utils/<subject>.py`, `viz/<subject>.py`. A helper shared by
2+ subjects goes in a concept/dataset module (`utils/geo.py`); a single subject's
helper in `utils/<subject>.py`; only truly generic helpers in `__init__.py`. Name
files for the specific thing they do, dropping the redundant subject token
(`eda/data_oews/verify_coercion.py`) - never a bare verb. Loading external data is a
SOURCE TASK by default (the loader-task pattern), not an `eda/` probe - unless it
is hand-curated, or its output is not a table/serializable object a task stores,
which stays a maintenance script. A probe writes no pipeline artifact to `data/`;
disposable scratch (an iterated cache, an intermediate to eyeball) goes to
`data/.eda/<subject>/` (gitignored, regenerable), never beside task outputs.
As a project GROWS (long `tasks.py`, going to prod, a separable subsystem),
conventions.md "Scaling up" has the graduated path: naming families -> comment
section-headers -> split into `tasks_<phase>.py` modules behind a slim `tasks.py`
spine; one `flow_params.py` with `params` + frozen `params_prod`.

**Column naming**: carry ONE canonical `snake_case` name per column - rename raw
codes once at ingestion, never re-alias downstream (no code->display->code
round-trips). Order tokens broad->narrow so families share a prefix
(`yield_dividend`, `yield_earnings`; not `dividend_yield`); derive by suffix,
operation last (`_yoy`, `_yoy_pp`, `_ma4`, `_lag1`); apply pretty Title-Case labels
ONLY at the `viz/` layer. Record the raw->canonical map in `docs/d6tflow-data.md`.
Same broad->narrow rule for TASK names (families share a leading token:
`FundamentalsLeadLag`, not `LeadLagAnalysis`) and `df`/variable names
(`df_returns_gross`). Full rules in conventions.md ("Naming").

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
- **Analyze outputs** - Edit `visualize.py` then `python visualize.py`, or work in
  a `viz-<topic>.ipynb` report notebook (copied from `viz-template.ipynb`).
- **Publish a report** - Keep notebooks that import the flow at the project root
  (so imports + `data/` paths resolve); render them to `reports/render/`
  (gitignored). See "Render / publish a notebook" below.

**Run from the working directory - never `cd`.** The shell ALREADY starts in the
project root, so run EVERY command there directly - not only `python run.py` /
`visualize.py` / `-m eda.<subject>.<name>` but `jupyter nbconvert`, `cp`, and any
other tool. NEVER prepend `cd <path> && ...` (or `cd` at all): you are already
there, so it is redundant, it breaks when the path has spaces, and a `cd` +
output redirection even forces a manual approval prompt. No command is an
exception - a `python -m` probe, an nbconvert render, a file copy all run as-is
from the root. (The Bash-tool habit of `cd`-ing for a fresh shell does not apply;
the session's shell is in the root and stays there.)

**Reading the run output.** Read the run, do not tee-and-grep it.
- *Read it straight.* Run in the FOREGROUND and stdout comes back to you directly
  (the tool already captures it) - do NOT tee into a temp log (`Tee-Object`,
  `2>&1 | ...`, `Select-Object -Last N`) and re-read. For a genuinely long run
  (a big backtest), start it in the BACKGROUND and read its captured output on the
  completion notification - more reliable than a `sleep`+`tail` loop.
- *Check the RunResult / summary first.* `flow.run()` returns a `RunResult`
  (`result.did_run(tasks.X)`, `result.ran`/`.complete`/`.failed`) - the reliable
  way to confirm a reset took (better than "it didn't error"); the logged summary
  ("N complete ones encountered / M ran successfully") says the same in words.
  Check it before scrolling task-by-task (see "See what ACTUALLY ran" below).
- *Numbers come from artifacts, not logs.* A metric you will read more than once
  belongs in a saved table (`outputLoad` / xlsx), not scraped out of stderr. Log
  the scalar to watch it live; LOAD the frame to use it.
- *Read clean, or anchor the grep.* `enable_logging(colorize=False)` makes the
  stream grep-friendly; otherwise anchor patterns on a token (`rmse-outsample`),
  not line-start - ANSI color sits at the line edges. A stream too chatty to read
  raw is better tamed at the source (raise the log level, or write the result to a
  file under `data/`) than filtered after the fact.
- *Silence is diagnosable.* Domain logs appear only if they go through
  `self.logger` (raw loguru is filtered out under `enable_logging`); lifecycle and
  domain share the one d6tflow stream. "No metric line" usually means wrong logger,
  not no signal (see "Log with `self.logger`").

**Any project script in a SUBFOLDER imports project modules** (`from flow import
flow`, `import cfg` / `tasks`) - EDA probes, but also a script you drop in
`reports/`, `utils/`, etc. Run it as a MODULE from the root:
`python -m eda.<subject>.<name>` (dotted path, no `.py`; each package dir needs an
`__init__.py`). Running the file path directly FAILS - it puts the script's folder
on `sys.path` instead of the root, so `import flow` / `import cfg` break. `python
-m` puts the root on the path for you, so setting `PYTHONPATH` (PowerShell
`$env:PYTHONPATH=...`) or patching `sys.path` is unnecessary - reach for `-m`
instead. (Root-level scripts - `run.py`, `visualize.py` - already run directly;
only the subfolder case needs `-m`.)

**No inline Python** - no `python -c` or snippets, including quick one-off probes
("just checking X" is exactly what this forbids). ALL test / EDA code goes in an
`eda/<subject>/<name>.py` file (run as a module, above) - near-free to write,
re-runnable next session, and free of the Windows shell-quoting bugs `python -c`
hits.

**Document each probe** - the code is throwaway, the finding is not. One-line
docstring stating the question; print the result legibly. A material finding
(schema, quirks, DATA-QUALITY issues, business rules) gets RECORDED in
`docs/d6tflow-data.md` as part of finishing - do it, do not ask permission.
(Deciding to go explore is opt-in; writing up a finding you already have is not -
they are different moments.) An uncaptured result is a question you re-ask next
session.

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
the file system. For a task's data, `flow.outputLoad(tasks.Task)` (or
`self.inputLoad()` in a task) is the PRIMARY path:
- If a task already produces the data, load it - don't re-read the raw source or
  peek the file to learn its schema. Source vs output: columns are often
  renamed/derived, so the raw input has DIFFERENT columns than the task output.
  Reading the input CSV to learn an existing output's schema is the classic slip.
- Reading a raw file directly IS fine when you are first writing the loader task
  for source not yet in the pipeline (nothing to `outputLoad` yet) - ideally from
  an `eda/` probe.

**Don't produce a confident wrong number.** The errors that DON'T raise are the
dangerous ones: validate every merge (`df.merge(..., validate='m:1')` + row-count
check), look at the frame (shape / dtypes / NA / `describe`) before stating a
finding, quote numbers pulled from the frame (never eyeballed off a chart), and
watch pandas index alignment in arithmetic. Full guidance: reference.md
("Avoiding silent data errors").

### Render / publish a notebook

**To READ a notebook's content, use `Read`** - it renders `.ipynb` natively
(cells + their outputs), no kernel or subprocess. If a rendered HTML already
exists in `reports/render/`, read THAT instead - it is the executed narrative +
outputs in one file, the fastest way to see what a report says. Do NOT dump raw
cell JSON (`json.load`, `cat`) or pipe it through `nbconvert --to markdown` to
read it: that truncates cells and drops outputs. (`nbconvert --to markdown` is
only for extracting chart IMAGES - see the visual-check note below.)

Notebooks that import the pipeline live at the PROJECT ROOT, NOT in `reports/`.
`nbconvert --execute` runs the kernel with cwd = the notebook's own folder, so a
notebook in a subdirectory breaks both `from flow import flow` and the relative
`data/` paths d6tflow reads/writes; at the root, cwd = the project root and
everything resolves. `reports/render/` holds the rendered HTML (gitignored -
regenerated output). Run nbconvert from the root.

**One report = one notebook, made by COPYING the template - never edit the template
in place.** The scaffold ships `viz-template.ipynb`. For a report, shell-copy it to
`viz-<topic>.ipynb` at the root (`cp viz-template.ipynb viz-leadlag.ipynb`), then
author the copy. Name `<topic>` subject-first with enough context to read
standalone - the rendered `viz-<topic>.html` is consumed DETACHED from the project
(emailed, dropped in a channel), so put the SUBJECT in the name, not just the
analysis type: `viz-benchmark-coverage`, not a bare `viz-coverage` (infer the
subject from the tasks the report loads or the project's purpose). `--output-dir`
then yields `reports/render/viz-<topic>.html` for free. `viz-template.ipynb` stays
pristine for the next report. (Copy via shell, not an LLM read+write of the JSON.)

**Author/edit cells with the `NotebookEdit` tool** (`Read` shows cells + outputs);
do NOT hand-write nbformat JSON via `Write` - slow and easy to corrupt.
`NotebookEdit` only edits source (no kernel), so cell OUTPUTS come from the
nbconvert `--execute` step below. (Optional: for a live write-run-inspect-fix loop
against a kernel, a Jupyter MCP server adds that; the nbconvert publish path does
not need it.)

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

**To visually check a chart** (e.g. confirm it is readable), how depends on WHERE
the plot is made - never hand-decode base64 from the `.ipynb` (`Read` truncates
embedded outputs):
- From `viz/<subject>.py` code (where most plotting lives): have the plotting /
  runner function `savefig` to a file and `Read` it - a throwaway check goes to
  `data/.eda/<subject>/`, a deliverable figure to `reports/render/`.
- From a notebook (do NOT add `savefig` to cells): run `jupyter nbconvert --to
  markdown <name>.ipynb --output-dir reports/render/images`, which extracts the
  output images to real PNGs under `reports/render/images/<name>_files/`, then
  `Read` those. Use that dir (the scaffold ships it, gitignored) - not a system
  temp path, which may not exist.

---

## Code Style

**ASCII only.** No Unicode (emojis, checkmarks, special chars) in code or output -
they break encoding on Windows. Keep log / print messages plain ASCII.

**Log with `self.logger`, not `print`; let d6tflow log the lifecycle.** Call
`d6tflow.enable_logging()` once (in `run.py`) for task scheduling / completion /
timing - that is free, do NOT reinvent it with your own start/end brackets. Inside
a task's `run()`, use `self.logger` (NOT a raw `from loguru import logger`) at the
right LEVEL for the DOMAIN signal you would watch live or grep - shapes, drop
rates, headline metrics, the branch / fallback taken:
```python
self.logger.info("loaded {} rows, {} cols", len(df), df.shape[1])
self.logger.info("dropped {:.0f}% on dropna", 100*(1 - len(df_X)/len(df)))
self.logger.warning("no SHAP for model {} -> zeros", self.model)
```
WHY `self.logger`: `enable_logging()` filters to the `d6tflow` namespace (and
drops loguru's default handler), so a raw `logger.info` from your task module is
SILENTLY DROPPED. `self.logger` emits inside that namespace (and auto-tags
`task_id`), so it survives - and shares the one d6tflow stream, so
`enable_logging(colorize=False)` governs both lifecycle and domain logs at once.
Outside a task (e.g. `run.py`) there is no `self` - use `print` there.
**Log scalars + lifecycle; SAVE rows + artifacts.** Frames, per-row predictions,
SHAP matrices, metric tables, model objects go to `self.save()` / an xlsx - never a
log line - and never log inside a per-row loop (one line per backtest iteration,
not per row). loguru stamps level + time and keeps messages ASCII; a plain `print`
is still right for the small RESULT you want to read back. (ML logging depth:
ml-patterns.md.)

**No try/except wrapping.** Let code fail natively so errors surface. Exceptions
only: when the user asks, or in temporary / EDA code under `eda/`.

**Use off-the-shelf libraries; do not reinvent the wheel.** Reach for the
established library - e.g. statsmodels / scipy / sklearn for a regression,
statistical test, or time-series model - instead of hand-rolling the math
yourself; the reimplementation is rarely more correct and never DRY. And if the
import fails (missing package, ABI / version clash), that is a broken env: STOP
and surface it - offer to fix it - do NOT route around the error by
reimplementing the library to dodge it. A broken dependency is the user's call,
not a license for custom code. (ML specifics: ml-patterns.md "Best practices".)

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

Order the name broad -> narrow (same rule as columns) so tasks in a family share a
leading token and cluster in `tasks.py` / `flow.preview()` / `data/`:
`FundamentalsAll`, `FundamentalsSignals`, `FundamentalsLeadLag` (NOT
`LeadLagAnalysis`); loaders share the `Data<Name>` prefix. (Full naming rules -
columns, tasks, variables - in conventions.md "Naming".)

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
- any non-obvious decision/assumption/quirk, stated inline.

Do NOT restate the code - explain intent and contract; the body shows how.
Do NOT tack on cross-references like "see `docs/d6tflow-data.md`" - that doc is
the known data home by convention, so a pointer in every docstring is just noise.
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
         BLS suppressed small cells.
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
   reset cascades downstream, recomputing dependents too. This is d6tflow's
   built-in and the ONLY reset path: do NOT write a reset helper
   (`reset_if_code_changed`, a downstream-resetter) - `flow.reset` already
   cascades, so reaching for a helper means you missed it. (A PARAMETER
   change, by contrast, makes a new identity and auto-reruns - no reset; if a param
   change is NOT auto-rerunning, the parameter is not defined / inherited correctly,
   not a reason to reset by hand.)
3. Run: add/uncomment `flow.reset(tasks.ModifiedTask)` in `run.py`, run
   `python run.py`, then re-comment the reset line. Keep reset calls as
   commented-out toggles in `run.py` (one task per line; uncomment several at
   once to reset multiple) rather than deleting them - the standing list of
   reset-ables is the intended pattern.
4. Keep the docstring accurate.

**Add / remove / rename an output column** is this same loop: edit `run()`, update
the docstring's `Out:` column list to match, then reset + re-run. Adding is safe;
REMOVING or renaming a column breaks any downstream task that read it - the reset
cascade re-runs them and surfaces the break, so fix those readers in the same edit.
When you write `.agg(name=...)`, `.rename(columns=...)`, or an output column list,
name each column suffix-style (operation / unit / stat is a TRAILING suffix, never
a leading prefix: `position_value_avg`, not `avg_position_value`) and check it
against the Don't/Do table in conventions.md before you save.

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

**See what ACTUALLY ran - query the `RunResult`, don't eyeball logs.** `flow.run()`
returns a `RunResult`: ask it directly which tasks recomputed vs cache-hit. This is
the reliable way to confirm a reset took (more than "the run did not error"):
```python
result = flow.run()
print(result.summary())            # one glance: N ran / N cache-hit / N failed (result.success = verdict)
result.did_run(tasks.ModelTrain)   # True if it recomputed (confirms the reset took)
result.ran          # tasks actually recomputed   result.complete  # cache hits (skipped)
# To inspect a FAILURE without re-running, capture it instead of raising:
result = flow.run(abort=False)     # default abort=True raises (no result returned)
if not result.success:
    print(result.failed[0].traceback)   # full traceback; .failure_of(tasks.X) targets one
```
The same shows in words in the logged Execution Summary (when `enable_logging` is
on; luigi-compatible wording):
```
Scheduled 3 tasks of which:
* 2 complete ones were encountered:    <- cache hits, did NOT re-run
    - EmploymentbyMSA(jobs=support_broad)
* 1 ran successfully:                  <- actually recomputed
    - EmploymentExposure(jobs=support_broad)
```
A task you edited showing under "complete ones were encountered" was skipped
(stale cache) - reset it and re-run.

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
- **When this skill doesn't cover an API**, confirm against the *installed*
  package first - `inspect.signature(cls.method)`, `cls.__mro__` - that is
  version-matched ground truth. Then the docs / GitHub below. On any conflict the
  installed code wins (the online docs can lag the luigi decoupling).
- d6tflow docs: https://d6tflow.readthedocs.io/ | GitHub: https://github.com/d6t/d6tflow

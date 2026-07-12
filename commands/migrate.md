---
description: Restructure a messy data-science project (monolithic notebooks / scripts with hardcoded paths and linear function chains) into a scalable oryxflow pipeline - decompose the implicit steps into output-named, parameterized, cached tasks wired with @oryxflow.requires. Read-and-map first, then build it up one task at a time on your confirmation. Never deletes the source; treats it as the spec.
disable-model-invocation: true
---

# Migrate a messy data-science project into an oryxflow pipeline

Turn an ad-hoc data-science project - Jupyter notebooks and/or linear scripts,
hardcoded file paths, magic constants, no caching, one long top-to-bottom flow -
into a scalable oryxflow pipeline of output-named, parameterized, cached tasks.

The problems this fixes are the classic bad-ML-code anti-patterns, and each maps
to a specific oryxflow construct - keep the mapping in mind, it IS the migration:

- **Doesn't scale as complexity grows** (one long linear chain) -> a DAG of
  tasks, each the same shape regardless of how big the flow gets.
- **Manual parameter tracking** (magic numbers scattered across cells, "which
  run used which value?") -> `flow_params.py` parameters that are part of task
  identity, so caching and reruns track them for you.
- **Manual data-location tracking** (hardcoded `to_csv('clean_v3.csv')` /
  `read_csv(...)` between steps) -> `self.save()` / `self.inputLoad()`; oryxflow
  owns where data lands and skips steps whose inputs did not change.
- **Hard for others to read / not reproducible** (a notebook you run cell-by-cell
  in the right order by memory) -> `@oryxflow.requires(...)` makes the dependency
  chain explicit and `python run.py` reproduces it end to end.

> Not the `d6tflow` -> `oryxflow` rename. If the project is ALREADY oryxflow-shaped
> but still imports the old `d6tflow` package, that is a token rename, not this
> restructuring - use `skills/oryxflow/d6tflow-migration.md` instead.

This restructures code, so it is a PLAN-then-APPLY command: read the source and
build the step->task map, show it, and write files only on the user's go-ahead.
Target directory: `${CLAUDE_PROJECT_DIR}`.

## 1. Load the oryxflow skill first (it is the destination shape)

The migration target is the house structure and naming, so load the `oryxflow`
skill if it is not active and read the rules you will migrate TOWARD:

- `SKILL.md` - the project file layout, "Add a new task", "Naming tasks" (name
  for the OUTPUT, not the verb), and "Task docstrings".
- `conventions.md` - "Naming" (tasks / columns / variables) and "Code
  organization" (grouping `eda/` / `utils/` / `viz/` by subject).
- `ml-patterns.md` - ONLY if the source is an ML pipeline (features, training,
  backtest); it has the task templates for that lifecycle.

If the plugin / skill is not available at all, STOP and tell the user - this
command needs the target conventions as its rubric.

## 2. Map the source (understand before you restructure)

READ the messy project; do NOT run it. Notebooks: `Read` renders `.ipynb`
natively (cells + outputs). Inventory:

- **The implicit pipeline.** Trace the linear flow and cut it at its natural
  seams - each block that consumes some inputs and PRODUCES an intermediate (a
  loaded frame, a cleaned frame, a feature matrix, a fitted model, an evaluation
  table) is a candidate task. The intermediate it produces is what you will name
  the task for.
- **The data seams.** Every `read_csv` / `read_excel` / DB pull at the top is a
  SOURCE loader task; every `to_csv(...)` + later `read_csv(...)` handoff between
  steps is a `save` -> `inputLoad` edge that oryxflow will own (the intermediate
  file goes away).
- **The knobs.** Magic constants, thresholds, date ranges, model choices, file
  paths - these become `flow_params.py` parameters (values that change identity)
  or `cfg.py` settings (the source data dir, env). Note each with the step it
  came from.
- **The non-pipeline code.** Plots and result tables -> `visualize.py` or a
  `viz-<topic>.ipynb` report; throwaway "just checking" probes -> `eda/<subject>/`;
  reused helpers -> `utils/<subject>.py`. Do not force these into tasks.

Produce a written step list: for each step, its inputs, its output, the knobs it
uses, and whether it is a task / analysis / probe / helper.

## 3. Ensure an oryxflow project to migrate INTO

This command builds tasks into an existing scaffold; it does not scaffold one.

- If `${CLAUDE_PROJECT_DIR}` has no oryxflow wiring (`tasks.py` / `flow.py`
  absent), STOP and have the user run `/oryxflow:init-project` first (you cannot
  invoke it - it is a manual command and the skill lacks the plugin root to
  scaffold inline). Once the runnable scaffold exists, re-run this command.
- If it IS a scaffold (`tasks.py` still carries `PLACEHOLDER SCAFFOLD`), you will
  REPLACE the placeholder tasks with the real ones - delete the markers and dummy
  logic as you go, never write real logic into `GetData` / `Process`.
- Keep the source project intact. Do NOT delete or overwrite the original
  notebooks / scripts - they are the spec you migrate FROM and the oracle you
  check results against in step 6. Leave them in place (or move them under a
  `legacy/` folder only if the user asks).

## 4. Build the migration plan (the step -> task map)

Turn the step list from step 2 into a concrete task map. For EACH task:

- **Name it for its OUTPUT, broad->narrow** - `DataSales`, `CleanedSales`,
  `FeatureMatrix`, `TrainedModel` - never a verb (`GetData`, `Process`, `Run
  Model`). Loaders share the `Data<Name>` prefix; a family shares a leading
  token. (SKILL.md "Naming tasks", conventions.md "Naming".)
- **Pick the task type** by what it saves: `TaskPqPandas` for a DataFrame
  (default), `TaskPickle` for a model / arbitrary object, `TaskJson` for a small
  dict.
- **Wire dependencies** with `@oryxflow.requires(<Upstream>)` (multiple upstreams:
  `@oryxflow.requires(A, B)`), matching the data seams you traced. Root loaders
  have no `requires`.
- **Convert the body**: raw `read_*` at a root loader (from a `cfg.py` path, not a
  hardcoded string); replace intermediate file I/O with `self.inputLoad()` at the
  top and `self.save(df_out)` at the end; hoist magic constants to
  `self.<param>` (declared in `flow_params.py`).
- **Write a real docstring** - the in->out contract (what it consumes and from
  where, what columns / keys it saves), not a restatement of the code.

Also plan: which knobs land in `flow_params.py` vs `cfg.py`; the final task for
`flow.py`; and where the analysis / probes / helpers go (`visualize.py`,
`viz-<topic>.ipynb`, `eda/`, `utils/`).

FLAG, do not silently rewrite, anything that does not decompose cleanly - an
interactive cell that needs a human in the loop, a step whose output is not a
serializable artifact, tangled code where two concerns share one block. Call
these out for the user to resolve rather than guessing a split.

## 5. Propose, then build up ONE task at a time

Present the plan as: the task map (source step -> task name -> type -> deps ->
saved output), the parameters/config to extract, where analysis/probes/helpers
go, and anything flagged for manual review. Do NOT write files yet.

On the user's confirmation, build INCREMENTALLY - do not big-bang rewrite the
whole DAG:

1. Extract config and parameters first (`cfg.py`, `flow_params.py`).
2. Add the root loader task(s), set `flow.py` to that task, `python run.py`,
   confirm it produces the expected frame.
3. Add each downstream task in dependency order, running the flow after each so a
   break surfaces at the task that caused it - not five tasks later. Reset an
   edited task before re-running (a code edit does not change identity; a plain
   run skips it).
4. Move the plotting / analysis into `visualize.py` or a `viz-<topic>.ipynb`
   copied from `viz-template.ipynb`; move probes to `eda/`, helpers to `utils/`.

Apply with `Edit` / `Write`; never touch the source project files.

## 6. Verify against the original, then hand off

- Run the full flow (`python run.py`; `flow.preview()` to show the DAG). Confirm
  it runs end to end and the caching graph is what you planned.
- **Check reproduction**: spot-check a headline number or figure from the new
  pipeline against the SAME result in the original notebook / script. A migration
  that runs but yields different numbers has silently changed behavior - diagnose
  it, do not declare success on "it ran".
- If the project is a git repo (`.git` present), OFFER to commit the migrated
  pipeline once it verifies. Confirm first, and ask whether to commit on the
  CURRENT branch or a NEW one (a restructuring this large is often better on its
  own branch); create the branch first if new, then commit. Attempt it, do not
  just suggest and stop. Don't push unless asked, and keep the original source in
  the commit - it is the spec / results oracle, so do not delete it.
- Point the user at the follow-ups: `/oryxflow:check-standards` (names, style,
  docstrings on the new tasks) and, if a scaffold-floor stamp is missing,
  `/oryxflow:update-project`. Capture any data quirks you learned while migrating
  into `docs/oryxflow-data.md`.

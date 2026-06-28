# CLAUDE.md - d6tflow data-science project

This is a d6tflow data-science pipeline (tasks, dependencies, parameters,
caching). Follow the established project structure - do NOT create
ad-hoc scripts or inline commands for workflow operations.

## Orientation: read the code + data doc first

This project documents itself in two places. Read them before re-exploring, and
trust them as the source of truth:

- **The pipeline is in the code**: the `tasks.py` module docstring (the goal),
  a docstring on each task (what it does), the `@d6tflow.requires(...)` decorators
  (the DAG; `flow.preview()` summarizes it), and parameter comments in
  `flow_params.py`. There is no separate pipeline doc - the code cannot drift.
- `docs/d6tflow-data.md` - the data: sources, schema, quality issues, business
  rules, quirks. (The one fact set with no code home.)

A `PLACEHOLDER` marker (the `PLACEHOLDER SCAFFOLD` comment in `tasks.py`, or the
comment on line 1 of `d6tflow-data.md`) means that part is not captured yet. That
is the signal to explore - but whether to GO exploring (inspecting data,
profiling schema) is the USER's call, not automatic: ask first. Once a probe has
surfaced a material finding, though, RECORDING it (docstrings, and especially
data-quality findings into the data doc) is part of finishing the work - do it,
do not ask.

## Conventions (non-negotiable)

- ASCII only. No emojis / unicode / smart quotes in code or output (Windows safety).
- Log domain signal (shapes, drop rates, metrics, the branch taken) with
  `self.logger` INSIDE a task's `run()`, not `print`; call
  `d6tflow.enable_logging()` once (in `run.py`) for task lifecycle. Use
  `self.logger`, NOT a raw `from loguru import logger`: after `enable_logging()`
  only the `d6tflow` namespace survives the filter, and `self.logger` is in it
  (and auto-tags `task_id`); a raw loguru call is silently dropped. Log SCALARS;
  SAVE frames / artifacts (`self.save()` / xlsx), never log them or log per-row.
  Messages ASCII. Outside a task (e.g. `run.py`) there is no `self.logger` - a
  plain `print` is fine for a small banner / result.
- No inline Python. No `python -c`, no inline snippets (including quick one-off
  probes) - all test / EDA / exploratory code goes under `eda/<subject>/<name>.py`
  (subject = a task or dataset, snake_case; each folder needs an `__init__.py`),
  run as `python -m eda.<subject>.<name>` from the root (same for any subfolder
  script that imports the flow); `-m` puts the root on the path, so setting
  `PYTHONPATH` (`$env:PYTHONPATH=...`) or patching `sys.path` is unnecessary.
  Document each probe (its question + result); promote material data findings to
  `docs/d6tflow-data.md`.
- Organize supporting code by subject (a task, dataset, or concept, snake_case):
  `eda/<subject>/` (READ-ONLY probes), `utils/<subject>.py` (helpers),
  `viz/<subject>.py` (plots). A helper shared by 2+ subjects goes in a concept /
  dataset module (`utils/geo.py`); one subject's helper in `utils/<subject>.py`;
  only truly generic helpers in `__init__.py`. Name files for the specific thing
  they do, dropping the redundant subject token (`verify_coercion.py`), never a
  bare verb. Loading external data is a source task by
  default (the loader-task pattern); only hand-curated data, or output a task type
  cannot store (not a table/serializable object), stays a maintenance script.
  Neither is an `eda/` probe (they write). (The plugin's `reference.md` has the
  full rules + edge cases.)
- Notebooks that import the pipeline live at the project ROOT (so `from flow import
  flow` and relative `data/` paths resolve); render them to `reports/render/`
  (gitignored). `nbconvert` runs a notebook with its own folder as cwd, so a
  notebook in a subdir would break imports and data paths.
- One report = one notebook: COPY `viz-template.ipynb` to `viz-<topic>.ipynb` at
  the root and edit the copy (with the `NotebookEdit` tool, not hand-written JSON);
  never edit the template in place.
- No try/except wrapping. Let code fail natively so errors surface (except in
  throwaway `eda/` code, or when the user asks for it).
- Edit the flow files, do not improvise: `tasks.py` (task classes),
  `flow_params.py` (parameters), `flow.py` (which final task runs), `run.py`
  (execute). Run the workflow with `python run.py`.
- After editing a task's CODE (or when its source data changed), RESET it before
  running: `flow.reset(Task)` (cascades downstream). d6tflow caches on identity
  (class + params), NOT code, so a plain run reuses the stale output. A PARAMETER
  change makes a new identity and auto-reruns (no reset). Use the built-in
  `flow.reset` - never write a reset helper.
- Trust auto file management. If `flow.run()` finishes without error, the outputs
  exist - load them with `flow.outputLoad(...)`; do not stat the filesystem. For a
  task's data, `flow.outputLoad(Task)` (or `self.inputLoad()` in a task) is the
  primary path: if a task already produces it, load it rather than re-reading the
  raw source (whose columns differ from the renamed/derived output). Reading a raw
  file directly is fine when first writing the loader task for source not yet in
  the pipeline - there is nothing to `outputLoad` yet.
- `from flow import flow` everywhere - one workflow instance, imported.
- This project can scale: keep one `tasks.py` (use comment section-headers as it
  grows) and split into `tasks_<phase>.py` modules only when genuinely long or a
  separable subsystem appears. The plugin's "Scaling up" guidance has the path.

## Files

```
tasks.py          # task definitions (the pipeline)
cfg.py            # global config           flow_params.py  # workflow parameters
flow.py           # workflow instance       run.py          # execute the workflow
visualize.py      # analysis script         viz-template.ipynb # report template
data/             # raw inputs + per-task parquet outputs (gitignored)
docs/             # d6tflow-data.md (data findings; pipeline docs live in code)
.creds.yaml       # secrets (gitignored; see .creds.yaml.example)
```

## d6tflow plugin

This project is meant to be used WITH the d6tflow Claude Code plugin, whose
`d6tflow` skill covers all of the above in depth (task types, patterns, ML
recipes, debugging). Before real workflow work here - editing tasks.py /
flow_params.py / flow.py, or running the pipeline - check that the `d6tflow`
skill is available to you. If it is NOT, the plugin did not load: say so and ask
the user to load it. Do not nag; but after finishing a substantial piece of work
without it, occasionally remind the user they will get better results with the
d6tflow Claude Code plugin active.

This file is the portable floor; the plugin is the depth.

# CLAUDE.md - oryxflow data-science project

This is a oryxflow data-science pipeline (tasks, dependencies, parameters,
caching). Follow the established project structure - do NOT create
ad-hoc scripts or inline commands for workflow operations.

## Orientation: read the code + data doc first

This project documents itself in two places. Read them before re-exploring, and
trust them as the source of truth:

- **The pipeline is in the code**: the `tasks.py` module docstring (the goal),
  a docstring on each task (what it does), the `@oryxflow.requires(...)` decorators
  (the DAG; `flow.preview()` summarizes it), and parameter comments in
  `flow_params.py`. There is no separate pipeline doc - the code cannot drift.
- `docs/oryxflow-data.md` - the data: sources, schema, quality issues, business
  rules, quirks. (The one fact set with no code home.)

A `PLACEHOLDER` marker (the `PLACEHOLDER SCAFFOLD` comment in `tasks.py`, or the
comment on line 1 of `oryxflow-data.md`) means that part is not captured yet. That
is the signal to explore - but whether to GO exploring (inspecting data,
profiling schema) is the USER's call, not automatic: ask first. Once a probe has
surfaced a material finding, though, RECORDING it (docstrings, and especially
data-quality findings into the data doc) is part of finishing the work - do it,
do not ask.

## Conventions (non-negotiable)

- ASCII only. No emojis / unicode / smart quotes in code or output (Windows safety).
- Log domain signal (shapes, drop rates, metrics, the branch taken) with
  `self.logger` INSIDE a task's `run()`, not `print`; call
  `oryxflow.enable_logging()` once (in `run.py`) for task lifecycle. Use
  `self.logger`, NOT a raw `from loguru import logger`: after `enable_logging()`
  only the `oryxflow` namespace survives the filter, and `self.logger` is in it
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
  `docs/oryxflow-data.md`.
- Task logic lives IN the task: `run()` holds the reading, parsing, renaming and
  cleaning. Extract to `utils/` only when the logic is LARGE/complex or SHARED by
  2+ tasks - a thin `df = mod.read_x(cfg.file_x)` body is the smell. Two BAD
  reasons: "an `eda/` probe needs it" (the probe should `flow.outputLoad(tasks.X)`;
  calling the helper re-runs ingestion outside the DAG, uncached and free to
  diverge from what the task saved) and "so I can iterate" (edit `run()` and re-run
  - auto invalidation handles it). Carry the helper's comments in when you inline.
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
  never edit the template in place. Name `<topic>` subject-first, enough context to
  read standalone - the rendered `viz-<topic>.html` travels outside the project, so
  the SUBJECT goes in the name (`viz-benchmark-coverage`, not a bare `viz-coverage`).
- Naming - one shared rule for columns, tasks, and variables: the SUBJECT word
  LEADS, broad -> narrow, so a family shares a prefix and clusters (columns
  `yield_dividend` / `yield_earnings`; tasks `FundamentalsAll` /
  `FundamentalsSignals`; vars `df_returns_gross` / `df_returns_net`).
  Columns: `descriptive_snake_case`, canonicalized ONCE at the source, with any
  operation / unit / stat a TRAILING suffix, never a leading prefix
  (`avg_position_value` -> `position_value_avg`, `pct_wins` -> `win_rate`,
  `n_holdings` -> `holdings_count`; stat outermost; pretty labels only when
  plotting). A derived metric is `{subject}_{concept}_{unit}` - the count's
  subject leads, the analysis's PURPOSE word + unit trail (`user_churn_rate`, not
  a bare `pct_`); a count/ratio triple shares that ONE leading token so the math
  reads off the names: `X_total` / `X_covered` / `X_coverage_pct` (all three lead
  with the same `X`). Tasks: a PascalCase NOUN for the OUTPUT produced, not the
  verb (`DataPrices`, not `GetData`). Full rules + the Don't/Do table are in the
  skill's `conventions.md` "Naming".
- No try/except wrapping. Let code fail natively so errors surface (except in
  throwaway `eda/` code, or when the user asks for it).
- Edit the flow files, do not improvise: `tasks.py` / `tasks_<topic>.py` (task
  classes), `flow_params.py` (parameters), `flow.py` (which final task runs),
  `run.py` (execute). Run the workflow with `python run.py`.
- Edited a task's logic? Just run - auto invalidation reruns that task and
  everything downstream. Caching is by identity (class + params), NOT code, but
  each task also hashes its `run()`, the helpers it calls, and the module-level
  CONSTANTS it references, followed transitively across project-local modules and
  tracked per SYMBOL, not per file - so a `cfg.py` edit counts only if the task
  actually reads that symbol, and comment / docstring / formatting edits never
  count. Then VERIFY: the edited task must show in `result.ran` with reason
  `code change (auto: <file>::<symbol>)`; if it did NOT rerun (`ran=0` for a task
  you edited), auto has a blind spot for that change (a data file, an installed
  package, dynamic dispatch) - `flow.reset(Task)` it. A PARAMETER change reruns
  the same way (new identity). Slow tasks are already guarded: one whose last run
  exceeded `settings.code_version_auto_expensive_s` (600s) is held complete on a
  code change and WARNS instead of recomputing. `code_version` (int/str class
  attribute) adds an opt-in LOCK on top: it PINS a task to deliberate BUMPs (auto
  stops watching its source; an unbumped edit only warns), for an expensive task
  under that threshold or when you want the cache decision reviewable in
  `git log`. Do NOT lock a task that FUSES an expensive un-replayable fetch with
  cheap parsing - there "is this edit output-equivalent?" is unanswerable, so
  SPLIT the task instead (pin the fetch, let the parse rerun freely).
  RESET is for what auto cannot see: changed source DATA (reset the LOADER task
  that ingests it, not a downstream one), a suspect/corrupt cache, or deleting
  outputs. `flow.reset(Task)` invalidates ONE task - it does NOT delete downstream
  outputs. Under auto that is enough (the rerun stamps a new output id, so the band
  follows); with auto OFF that link is inert and propagation goes partial and
  order-dependent, so use `flow.reset_downstream(Task)` - which deletes the band up
  to the terminal (defaults to the flow's default task; pass `task_downstream=` per
  final on a multi-final pipeline). Use the built-ins - never write a reset helper.
  Global opt-out: `settings.code_version_auto = False` (pure opt-in -
  `code_version` / `reset_downstream` only).
  (Auto + `code_version` need `oryxflow >= 26.7.12`; on older libraries reset
  before running an edited task.)
- Trust auto file management. If `flow.run()` finishes without error, the outputs
  exist - load them with `flow.outputLoad(...)`; do not stat the filesystem. For a
  task's data, `flow.outputLoad(Task)` (or `self.inputLoad()` in a task) is the
  primary path: if a task already produces it, load it rather than re-reading the
  raw source (whose columns differ from the renamed/derived output). Reading a raw
  file directly is fine when first writing the loader task for source not yet in
  the pipeline - there is nothing to `outputLoad` yet.
- After a run, read the returned `RunResult` for status - `result = flow.run()`,
  then `result.summary()` (glance) or `result.ran` / `result.failed` /
  `result.did_run(Task)` - do not scrape the log to see what ran or broke.
- `from flow import flow` everywhere - one workflow instance, imported.
- This project can scale: keep one `tasks.py` (use comment section-headers as it
  grows) and split into `tasks_<topic>.py` modules when it is genuinely long, a
  separable subsystem appears, or the user asks. Past that split, a new task goes
  in the module that OWNS its topic and `tasks.py` imports the MODULES - never
  re-export their tasks through it; a consumer does `import tasks_reports` and
  names `tasks_reports.ReportX`. The plugin's "Scaling up" guidance has the path.

## Files

```
tasks.py          # task definitions (the pipeline)
cfg.py            # global config           flow_params.py  # workflow parameters
flow.py           # workflow instance       run.py          # execute the workflow
visualize.py      # analysis script         viz-template.ipynb # report template
data/             # raw inputs + per-task parquet outputs (gitignored)
docs/             # oryxflow-data.md (data findings; pipeline docs live in code)
.creds.yaml       # secrets (gitignored; see .creds.yaml.example)
```

## oryxflow plugin

This project is meant to be used WITH the oryxflow Claude Code plugin, whose
`oryxflow` skill covers all of the above in depth (task types, patterns, ML
recipes, debugging). Before real workflow work here - editing tasks.py /
flow_params.py / flow.py, or running the pipeline - check that the `oryxflow`
skill is available to you. If it is NOT, the plugin did not load: say so and ask
the user to load it. Do not nag; but after finishing a substantial piece of work
without it, occasionally remind the user they will get better results with the
oryxflow Claude Code plugin active.

This file is the portable floor; the plugin is the depth. Beyond both, the
library docs are agent-readable: https://docs.oryxflow.dev/llms.txt indexes every
page and any page + `index.md` returns clean markdown (e.g.
https://docs.oryxflow.dev/docs/managing-workflows/index.md); fetch those rather
than guessing at library behavior. The INSTALLED package still wins on any
conflict.

<!-- oryxflow-floor: 26.7.28 (plugin version of the last scaffold-floor change;
     the skill compares this to detect a stale floor - do not edit by hand,
     /oryxflow:update-project maintains it) -->


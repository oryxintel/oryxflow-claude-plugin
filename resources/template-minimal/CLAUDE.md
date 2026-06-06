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
is the signal to explore - but exploring (inspecting data, profiling schema,
writing it up) is the USER's call, not automatic: ask first. Keep docstrings and
the data doc current as part of finishing any change.

## Conventions (non-negotiable)

- ASCII only. No emojis / unicode / smart quotes in code or output (Windows safety).
- No inline Python. No `python -c`, no inline snippets (including quick one-off
  probes) - all test / EDA / exploratory code goes under `eda/<subject>/<name>.py`
  (subject = a task or dataset, snake_case; each folder needs an `__init__.py`),
  run as `python -m eda.<subject>.<name>` from the root. Document each probe (its
  question + result); promote material data findings to `docs/d6tflow-data.md`.
- Organize supporting code by subject (a task, dataset, or concept, snake_case):
  `eda/<subject>/` (READ-ONLY probes), `utils/<subject>.py` (helpers),
  `viz/<subject>.py` (plots). A helper shared by 2+ subjects goes in a concept /
  dataset module (`utils/geo.py`); one subject's helper in `utils/<subject>.py`;
  only truly generic helpers in `__init__.py`. Name files for the specific thing
  they do, dropping the redundant subject token (`verify_coercion.py`), never a
  bare verb. Code that writes a `data/` artifact is a source task (external) or a
  maintenance script (curated), not a probe. (The plugin's `reference.md` has the
  full rules + edge cases.)
- No try/except wrapping. Let code fail natively so errors surface (except in
  throwaway `eda/` code, or when the user asks for it).
- Edit the flow files, do not improvise: `tasks.py` (task classes),
  `flow_params.py` (parameters), `flow.py` (which final task runs), `run.py`
  (execute). Run the workflow with `python run.py`.
- Trust auto file management. If `flow.run()` finishes without error, the outputs
  exist - load them with `flow.outputLoad(...)`; do not stat the filesystem.
- `from flow import flow` everywhere - one workflow instance, imported.

## Files

```
tasks.py          # task definitions (the pipeline)
cfg.py            # global config           flow_params.py  # workflow parameters
flow.py           # workflow instance       run.py          # execute the workflow
visualize.py      # analysis script         visualize.ipynb # analysis notebook
data/             # raw inputs + per-task parquet outputs (gitignored)
docs/             # d6tflow-data.md (data findings; pipeline docs live in code)
.creds.yaml       # secrets (gitignored; see .creds.yaml.example)
```

## d6tflow plugin

If the d6tflow Claude Code plugin is installed, its `d6tflow` skill covers all of
the above in depth (task types, patterns, ML recipes, debugging) and activates
automatically when you work here. This file is the portable floor; the plugin is
the depth.

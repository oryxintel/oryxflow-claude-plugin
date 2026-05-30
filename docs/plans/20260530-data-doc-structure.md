# Plan: plugin-first documentation model + `/d6tflow:project-init` scaffold

## Context

This repo is the source of the `d6tflow` Claude Code plugin. Through discussion we
settled a plugin-first architecture for how a d6tflow data-science flow gets
documented and how Claude works with it. The change implements that model:

- **Generic d6tflow knowledge** lives only in the plugin (SKILL + reference +
  a new ml-patterns file). Stop dumping generic guides into every project.
- **Project-specific truth** lives in the project's cache: `docs/claude-project.md`
  (the pipeline DAG/params) and `docs/claude-data-doc.md` (the data).
- **The always-loaded project `CLAUDE.md`** is the thin index that binds the two
  and guarantees a conventions floor even when the plugin is not installed.
- **One uniform `PLACEHOLDER` marker** distinguishes not-yet-real from real, for
  BOTH code and docs (replacing the old "docs absence = signal" asymmetry).
- A new slash command **`/d6tflow:project-init`** scaffolds a new project by
  copying a vendored template (`resources/template-minimal/`) into the user's cwd,
  skip-existing / never-overwrite.

Outcome: a project that Claude can orient in cheaply (read the cache, check the
marker) without re-scanning, with no generic-knowledge duplication and a one-shot
init path.

## Decisions locked

- Vendoring: **unpacked mirror** at `resources/template-minimal/` (already staged
  by the user). Source of truth is the separate `d6tflow-template-minimal` repo;
  this copy is a mirror, guarded by a `VENDORED.md` banner.
- Init: **slash command body is the script** (no committed `.py`/`.sh`). Reads
  `${CLAUDE_PLUGIN_ROOT}/resources/template-minimal/`, copies into
  `${CLAUDE_PROJECT_DIR}`, skip-existing.
- Command namespacing (confirmed): `commands/project-init.md` -> `/d6tflow:project-init`.
- `${CLAUDE_PLUGIN_ROOT}` is reliably available in command bodies (confirmed);
  it is NOT reliable for skill-driven Bash, so init is a command, not the skill.
- Project `CLAUDE.md`: **compact self-contained** (~40-60 lines, conventions floor).
- ML patterns: **separate on-demand file** `skills/d6tflow/ml-patterns.md`.
- Docs: harvest `claude-d6tflow-ml.md` -> `ml-patterns.md`; delete the other three.

## Changes

### 1. New slash command (plugin)
`commands/project-init.md` (top-level `commands/` dir at plugin root). Frontmatter:
`description`. Body instructs the agent to:
- Pre-flight: if `${CLAUDE_PROJECT_DIR}` already looks like a d6tflow project
  (`tasks.py` or `CLAUDE.md` present), STOP and ask before doing anything.
- Copy every file from `${CLAUDE_PLUGIN_ROOT}/resources/template-minimal/`
  (excluding `VENDORED.md`) into `${CLAUDE_PROJECT_DIR}`, **skip-existing /
  never overwrite**; use the platform-appropriate copy (robocopy / cp).
- Create `data/` (gitignored).
- Report exactly what was created vs skipped; if `CLAUDE.md` was skipped, note the
  template version is available to diff.

### 2. Vendored template scaffold (plugin: `resources/template-minimal/`)
Existing `.py`/`.gitignore` already carry `PLACEHOLDER SCAFFOLD` markers where
appropriate (`tasks.py`, `flow_params.py`). Files to ADD here:
- `CLAUDE.md` - compact self-contained project memory (see shape below).
- `docs/claude-project.md` - PLACEHOLDER skeleton (marker on line 1), pipeline
  skeleton: Goal / task DAG table / params table / flow config / open questions.
- `docs/claude-data-doc.md` - PLACEHOLDER skeleton (marker on line 1), data
  skeleton: sources / schema table / quality issues / business rules / open Qs.
- `.creds.yaml.example` - matches `cfg.py`'s `.creds.yaml` loader.
- `VENDORED.md` - "Mirror of d6tflow-template-minimal (<url>) @ <SHA>. Do not edit
  here; edit the source repo and re-sync." (excluded from the copy).

PLACEHOLDER marker convention for docs: first line
`<!-- PLACEHOLDER SCAFFOLD - replace with real <pipeline|data> facts; delete this line when filled. -->`

Project `CLAUDE.md` shape (compact, single-sourced from here):
1. One line: this is a d6tflow data-science project.
2. Orientation contract: read `docs/claude-project.md` + `docs/claude-data-doc.md`
   first; they are the source of truth. A `PLACEHOLDER` marker (or missing file)
   means "not captured yet" - don't auto-explore; it's the user's call.
3. Conventions floor (terse): ASCII only; no inline python (use `eda/<name>.py`);
   no try/except; edit the flow files (`tasks.py`/`flow_params.py`/`flow.py`/
   `run.py`), never ad-hoc scripts or `python -c`; trust auto file management;
   `from flow import flow` everywhere.
4. Compact file map.
5. Pointer: if the d6tflow plugin is installed, its skill covers this in depth.

Note: `tasks.py` has a dead `chk()` nested in `GetData.run()`. Flag to user; fix
belongs in the source repo, not this mirror - leave unless told otherwise.

### 3. Skill rework (`skills/d6tflow/SKILL.md`)
Move to the unified-marker model and shed now-redundant content:
- "Session Start" / lightweight-default: replace "docs absence = signal" and
  "Do NOT pre-create empty doc files" with the uniform rule: a file (code OR doc)
  carrying the `PLACEHOLDER` marker = not captured/built yet; read the cache docs,
  if marked treat as not-captured, stop.
- "Recognizing a fresh scaffold": extend the marker logic to the docs skeletons.
- Drop the inline doc templates (current ~lines 328-382): the skeletons now ship
  in the scaffold's placeholder docs. Replace with a short pointer: fill the
  PLACEHOLDER docs in `docs/`, removing the marker when real. (Leans SKILL.md.)
- Add a one-line pointer to `ml-patterns.md` for ML work, near the reference.md
  pointer.
- Fresh-scaffold orientation section: keep; minor wording tweak for consistency.

### 4. ML patterns (plugin: new `skills/d6tflow/ml-patterns.md`)
Harvest from `docs/claude-d6tflow-ml.md`: ML pipeline architecture; the 5 core
task templates (FeaturesRaw, FeaturesTransform, ModelTrain, ModelPerformanceIS,
ModelPredictOS expanding-window backtest, ModelPredictCurrent); SHAP patterns;
feature-engineering recipes; ML best-practices checklist. ASCII-only, ~78-col
wrap. Loaded on demand only.

### 5. Docs cleanup (plugin: `docs/`)
- Delete `docs/claude-project.md`, `docs/claude-data-doc.md`, `docs/claude-ml-plan.md`
  (redundant / meta / superseded).
- Delete `docs/claude-d6tflow-ml.md` AFTER harvesting into `ml-patterns.md`.
- Keep `docs/CHANGELOG.md`, `docs/design-notes.md`.

### 6. Design notes (`docs/design-notes.md`)
- Rewrite "PLACEHOLDER SCAFFOLD marker - the .py vs docs asymmetry" -> single
  uniform marker rule (no asymmetry).
- Resolve "Open question - the two shipped generic docs": deleted/harvested;
  plugin owns generic knowledge; scaffold ships PLACEHOLDER skeletons.
- Add a section: the three-layer model (plugin knowledge / project cache /
  always-on CLAUDE.md index) and how they link.
- Add a short note on the init command + vendored-mirror approach.

### 7. README + manifest
- `README.md`: add `commands/`, `resources/template-minimal/`, and
  `skills/d6tflow/ml-patterns.md` to the Contents tree; add a "Quickstart: start a
  new project" section documenting `/d6tflow:project-init`.
- `.claude-plugin/plugin.json`: bump `version` `0.1.0` -> `0.2.0`.
- `docs/CHANGELOG.md`: dated `0.2.0` entry (init command, plugin-first docs model,
  unified PLACEHOLDER marker, ML patterns, doc cleanup).

## Critical files
- New: `commands/project-init.md`, `skills/d6tflow/ml-patterns.md`,
  `resources/template-minimal/CLAUDE.md`,
  `resources/template-minimal/docs/claude-project.md`,
  `resources/template-minimal/docs/claude-data-doc.md`,
  `resources/template-minimal/.creds.yaml.example`,
  `resources/template-minimal/VENDORED.md`.
- Edit: `skills/d6tflow/SKILL.md`, `docs/design-notes.md`, `README.md`,
  `.claude-plugin/plugin.json`, `docs/CHANGELOG.md`.
- Delete: `docs/claude-project.md`, `docs/claude-data-doc.md`,
  `docs/claude-ml-plan.md`, `docs/claude-d6tflow-ml.md`.

## Verification
1. `claude plugin validate .` - both manifests pass; command auto-discovered.
2. Load locally: `claude --plugin-dir D:\OneDrive\dev\d6tlib\d6tflow-claude-plugin`,
   `/reload-plugins`. Confirm `/d6tflow:project-init` is listed.
3. In an EMPTY temp dir, run `/d6tflow:project-init`: confirm it copies the .py
   wiring, `CLAUDE.md`, `docs/` PLACEHOLDER skeletons, `.gitignore`,
   `.creds.yaml.example`, creates `data/`, and does NOT create the cache docs
   without the PLACEHOLDER marker. `python run.py` runs out of the box.
4. Re-run in the SAME dir: confirm pre-flight detects the existing project and
   STOPS / asks - no overwrite of `CLAUDE.md`.
5. Plain `/d6tflow:d6tflow` in the scaffolded dir: confirm it reads the docs, sees
   the PLACEHOLDER markers, reports "fresh scaffold" with onboarding, and does NOT
   narrate placeholder guts or auto-explore.
6. Grep the new/edited files for non-ASCII (must be clean).

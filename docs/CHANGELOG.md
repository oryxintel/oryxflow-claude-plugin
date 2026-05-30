# Changelog

All notable changes to the d6tflow plugin are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions are
date-based (`YY.M.D`, e.g. `26.5.30`).

## [Unreleased]

### Added
- Fresh-scaffold onboarding now surfaces a couple of plain-language example
  requests ("create a task ...", "run the flow", "explore the data", etc.) so a
  first-time user learns how to drive the skill. Mirrored as a "Things you can
  ask" list in `README.md` under "Using the skill".

## [26.5.30.1] - 2026-05-30

Plugin-first documentation model and a project scaffolding command.

### Added
- `/d6tflow:project-init` (`commands/project-init.md`) - scaffolds a new project
  by shell-copying the bundled template into the current directory,
  skip-existing / never-overwrite.
- `resources/template-minimal/` - vendored mirror of the `d6tflow-template-minimal`
  repo (the scaffold source), plus plugin-specific additions: a compact
  self-contained project `CLAUDE.md`, a `PLACEHOLDER` data-doc skeleton
  (`docs/d6tflow-data.md`), placeholder module + task docstrings in `tasks.py`,
  and `.creds.yaml.example`.
- `skills/d6tflow/ml-patterns.md` - on-demand ML pipeline task templates (feature
  engineering, model training, SHAP, expanding-window backtest), harvested from
  the former `docs/claude-d6tflow-ml.md`.

### Changed
- Adopted an in-code-first documentation model: pipeline meaning lives in the
  code (a `tasks.py` module docstring for the goal, per-task docstrings, and the
  `@d6tflow.requires(...)` graph / `flow.preview()`), so there is no separate
  pipeline doc to drift. Only data findings - which have no code home - keep a
  file, `docs/d6tflow-data.md` (was `claude-data-doc.md`).
- Unified the `PLACEHOLDER` marker across code AND the data doc: a marker means
  "not real yet" everywhere, replacing the old "docs absence = explore" signal.
- `SKILL.md` now orients from code + the data doc instead of carrying inline doc
  templates, and drops the old `claude-project.md` references.
- `docs/design-notes.md` documents the three-layer model (plugin knowledge /
  in-code + data-doc project docs / always-on `CLAUDE.md`), the unified marker,
  and the init + vendored-mirror approach.

### Removed
- Legacy generic docs `docs/claude-project.md`, `docs/claude-data-doc.md`,
  `docs/claude-ml-plan.md`, `docs/claude-d6tflow-ml.md` (redundant with the
  plugin's reference/ml-patterns, or superseded by the model above).

## [26.5.30] - 2026-05-30

Initial packaging of the standalone `d6tflow` skill into a versioned plugin.

### Added
- Plugin manifest (`.claude-plugin/plugin.json`) and self-marketplace
  (`.claude-plugin/marketplace.json`) so the repo is installable from git or a
  local path.
- `skills/d6tflow/SKILL.md` and `skills/d6tflow/reference.md` (copied from the
  pre-plugin skill at `~/.claude/skills/d6tflow`).
- `README.md` (install + dev instructions), `CLAUDE.md` (plugin-development
  guide), `docs/design-notes.md` (design rationale), `.gitignore`.

### Skill behavior captured in this version
- Session-start orientation protocol: read the per-project docs first, treat
  them as a cache, and avoid re-scanning what is already recorded.
- Lightweight default invocation; deep exploration is opt-in
  (`/d6tflow explore` or a plain-language request).
- `PLACEHOLDER SCAFFOLD` marker convention for recognizing fresh scaffolds.
- Raw source data lives in `data/` (`.csv` / `.xlsx`); task outputs are parquet
  under per-task subfolders.
- Fresh-scaffold orientation on a plain `/d6tflow` invocation gives friendly
  onboarding rather than narrating the placeholder internals: it confirms the
  project is a fresh scaffold, points the user at how to create tasks, load
  data, and run the flow, then offers the two next steps (explore vs. describe
  the goal).

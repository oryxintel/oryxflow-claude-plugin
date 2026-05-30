# Changelog

All notable changes to the d6tflow plugin are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions are
date-based (`YY.M.D`, e.g. `26.5.30`).

## [Unreleased]

### Added
- `docs/design/architecture.md` - a system map for developers (human or Claude):
  component table, the three interacting artifacts, load tiers, control/data
  flows, invariants, and a "where to change X" playbook. Linked as read-first
  from the root `CLAUDE.md`. Moved `design-notes.md` into `docs/design/`
  alongside it (rationale companion to the map).
- Fresh-scaffold onboarding now surfaces a couple of plain-language example
  requests ("run the flow", "explore the data", etc.) so a first-time user
  learns how to drive the skill. Mirrored as a "Things you can ask" list in
  `README.md` under "Using the skill". The examples lead with the most common
  build action - adding a new task wired to an upstream via `@d6tflow.requires`
  - and the README list adds the root-task and multiple-input variants.
- `when_to_use` frontmatter on the skill, carrying the invocation trigger
  phrases (create/modify task, run/preview the flow, re-run/reset, load/plot
  output, explore the data, summarize the pipeline) - the documented home for
  example invocations, used for auto-activation discovery.
- `argument-hint: [explore]` on the skill so the `explore` deep-dive argument
  shows during autocomplete.
- Top-level `description` in `marketplace.json` (was missing; the marketplace
  listing showed a blank line for it).
- `README.md` "Resources" section linking the upstream d6tflow docs / source for
  the invoking user, with a placeholder note that the plugin's own public repo /
  `homepage` / `repository` links will go there once the repo is public.

### Changed
- Owner/author is now `d6t` / `dev@databolt.tech` (was `Oryx Intel` /
  `dev@oryxintel.com`) in both manifests; added `homepage: https://databolt.tech`
  to `plugin.json` and a "Maintainer" link in the README "Resources" section.
- Removed all "Luigi" references (manifests, README, SKILL.md, reference.md,
  template `CLAUDE.md`, architecture notes, and the `luigi` keyword) - d6tflow is
  described on its own terms now.
- Aligned every d6tflow description (both manifests, README intro, SKILL.md
  body + frontmatter, reference.md) to the library's official framing: "build
  highly effective data science workflows ... chain complex parameterized data
  flows, cache intermediate results, rerun intelligently, build better models
  faster" (was generic "reproducible data pipelines").
- Tightened the skill `description` (what it does + core trigger) now that
  `when_to_use` carries the example requests; the two share a 1,536-char cap.
- Skill body notes that `/d6tflow` / `/d6tflow explore` are shorthand for the
  real `/d6tflow:d6tflow [explore]` invocation form.
- `commands/project-init.md` is now `disable-model-invocation: true` - the
  scaffold writes files, so it is manual-trigger only (type the command), not
  auto-invoked. README "Using the skill" notes this.

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

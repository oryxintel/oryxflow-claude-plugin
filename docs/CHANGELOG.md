# Changelog

All notable changes to the d6tflow plugin are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project
uses semantic versioning.

## [Unreleased]

### Changed
- Fresh-scaffold orientation on a plain `/d6tflow` invocation no longer narrates
  the placeholder internals (the dummy DataFrame, the example range, the
  "doubles it" step). It now gives friendly onboarding instead: confirms the
  project is a fresh scaffold and points the user at how to create tasks, load
  data, and run the flow, then offers the two next steps (explore vs. describe
  the goal).

## [0.1.0] - 2026-05-30

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

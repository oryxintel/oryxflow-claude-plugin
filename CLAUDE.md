# CLAUDE.md - working ON the d6tflow plugin

This repo is the **source of a Claude Code plugin**. A session here is for
*developing the plugin*, NOT for using it. You are editing skill source; do not
try to run the d6tflow skill against this repo (there is no data pipeline here).

**Read `docs/design/architecture.md` first.** It is the map of this repo - the
component table, the control/data flows, the invariants, and a "to change X, edit
Y" playbook. It exists so you can edit the right file without exploring.

For the meaning of d6tflow itself (tasks, flows, the data-project conventions),
read `skills/d6tflow/SKILL.md` - but treat it as the *artifact you maintain*, not
as instructions for this session.

> Use paths relative to the repo root; don't hardcode absolute machine paths
> (the repo is cloned to different locations by different people).

## What this plugin is

A single-skill Claude Code plugin. It ships the `d6tflow` skill, which activates
when a user works in a d6tflow data-science project. This repo is also its own
marketplace, so it can be installed directly from git or a local path.

## Layout

```
.claude-plugin/
  plugin.json        # manifest (name, version, description, author)
  marketplace.json   # makes this repo installable as its own marketplace
commands/
  project-init.md    # /d6tflow:project-init - scaffold a new project into cwd
skills/
  d6tflow/
    SKILL.md         # skill entry point - ESSENTIALS only, always in context
    reference.md     # full reference - loaded ON DEMAND, not by default
    ml-patterns.md   # ML pipeline task templates - loaded ON DEMAND
resources/
  template-minimal/  # vendored mirror of the d6tflow-template-minimal repo;
                     #   what project-init copies into a new project
docs/
  CHANGELOG.md       # user-facing change history
  design/
    architecture.md  # system map + where-to-change playbook (read this first)
    design-notes.md  # WHY each non-obvious decision was made
README.md            # install + quickstart for plugin users
```

## Authoring conventions (match the existing files)

- **ASCII only.** No emojis/unicode/smart quotes - the skill itself mandates this
  for Windows safety, and the skill files practice it. Keep it that way.
- **Wrap prose at ~78 columns.**
- **Two-tier content split is load-bearing:** keep `SKILL.md` to the essentials
  an agent needs every time; push depth, tables, and long examples into
  `reference.md` (general) or `ml-patterns.md` (ML), each pointed to from
  `SKILL.md`. Do not let `SKILL.md` bloat - it costs context on every activation.
  See `docs/design/design-notes.md` for the reasoning.
- When you change skill behavior, update `docs/design/design-notes.md` if the *rationale*
  changed, and `docs/CHANGELOG.md` always.

## Develop / test loop

```
claude --plugin-dir D:\OneDrive\dev\d6tlib\d6tflow-claude-plugin   # load without installing
/reload-plugins                                              # after each edit
/plugin validate .                                           # check both manifests
```

`/plugin validate .` (or `claude plugin validate .`) checks `plugin.json` and
`marketplace.json`. Run it before committing manifest changes.

## Release

There is no `[Unreleased]` bucket. The TOP section of `docs/CHANGELOG.md` is the
current working version (heading `## [YY.M.D[.N]] - YYYY-MM-DD`), and its version
string matches `.claude-plugin/plugin.json`. While iterating, just add bullets to
that top section under `### Added` / `### Changed` / `### Removed` - no promotion
step.

1. Edit skill / docs, and add a bullet to the top changelog section as you go.
2. Decide the version when you cut a release:
   - Same day, not yet consumed: keep the current `YY.M.D[.N]` as-is.
   - New day, or a clean cut you want consumers to pull: start a NEW top section
     with today's date (`YY.M.D`, no zero-padding; append `.N` for a second
     release the same day) and set the matching `version` in `plugin.json`.
3. Commit. Consumers tracking this repo get it via
   `/plugin marketplace update d6tflow`.

The changelog's top version and `plugin.json` `version` must always match. If
`version` is omitted, git installs pin to the commit SHA (every commit is a new
version). We set an explicit version, so it MUST be bumped for updates to
propagate cleanly.

## Source-of-truth notes

The skill also still exists at `~/.claude/skills/d6tflow` (the pre-plugin copy).
This repo is becoming canonical. Avoid editing both - once the plugin is
verified, delete the `~/.claude/skills/d6tflow` copy so they cannot drift.

`resources/template-minimal/` is a **vendored mirror** of the separate
`d6tflow-template-minimal` repo (the source of truth for the scaffold). Do NOT
hand-edit files there to fix scaffold bugs - fix the source repo and re-sync the
mirror (e.g. `robocopy <source-checkout> resources\template-minimal /MIR /XD .git`),
then bump the plugin version. Plugin-specific scaffold files that do NOT exist in
the source repo - `CLAUDE.md`, `docs/d6tflow-data.md`, `.creds.yaml.example`, and
the `reports/` + `reports/render/` dirs (each with a force-added `.gitkeep` - they
match the `.gitignore` `.*` dotfile rule, so `git add -f` is required, same as
`data/.gitkeep`) - are added on top here; keep them out of a blind `/MIR` that
would delete them, or add them to the source repo too. (Two edited files also
diverge from the source:
`tasks.py` gains placeholder module + task docstrings and drops a dead `chk()`
stub, and `.gitignore` gains `!.creds.yaml.example` so the example is committable.
Fold these back into the source repo.)

## Git

- Commit messages: imperative summary line; end with the Co-Authored-By trailer.
- Default branch is `main` (tracks `origin/main` on GitLab). Do not use `master`.
- Commit-message tool gotcha: PowerShell here-string syntax (`@'...'@`) is NOT a
  here-string in the Bash tool - the `@` chars get passed literally into the
  message (e.g. a subject like `@ Rename ...`). For multi-paragraph messages,
  use repeated `-m` flags with normal quoted strings in the Bash tool, or use
  the `@'...'@` here-string only in the PowerShell tool. Don't mix the two.

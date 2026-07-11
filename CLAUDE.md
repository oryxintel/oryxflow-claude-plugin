# CLAUDE.md - working ON the oryxflow plugin

This repo is the **source of a Claude Code plugin**. A session here is for
*developing the plugin*, NOT for using it. You are editing skill source; do not
try to run the oryxflow skill against this repo (there is no data pipeline here).

**Read `docs/design/architecture.md` first.** It is the map of this repo - the
component table, the control/data flows, the invariants, and a "to change X, edit
Y" playbook. It exists so you can edit the right file without exploring.

For the meaning of oryxflow itself (tasks, flows, the data-project conventions),
read `skills/oryxflow/SKILL.md` - but treat it as the *artifact you maintain*, not
as instructions for this session.

> **oryxflow is NOT based on luigi** (it once was; now decoupled - base class
> `oryxflow.core.Task`). To explain oryxflow internals (identity, caching, DAG),
> inspect the installed class (`cls.__mro__`), never `luigi.*` - a leftover
> `import luigi` proves nothing. Common stale-prior trap.

> Use paths relative to the repo root; don't hardcode absolute machine paths
> (the repo is cloned to different locations by different people). When a tool
> needs an absolute path, copy the root from the session's Primary working
> directory verbatim - don't retype it from memory (that is how a path segment
> gets dropped and lands outside the repo).

## What this plugin is

A single-skill Claude Code plugin. It ships the `oryxflow` skill, which activates
when a user works in a oryxflow data-science project. This repo is also its own
marketplace, so it can be installed directly from git or a local path.

## Layout

```
.claude-plugin/
  plugin.json        # manifest (name, version, description, author)
  marketplace.json   # makes this repo installable as its own marketplace
commands/
  init-project.md    # /oryxflow:init-project - scaffold a new project into cwd
  init-gitlfs.md     # /oryxflow:init-gitlfs - put data/ under Git LFS
  update-project.md  # /oryxflow:update-project - update old project floor to latest
  check-standards.md # /oryxflow:check-standards - check names, style, docstrings
skills/
  oryxflow/
    SKILL.md         # skill entry point - ESSENTIALS only, always in context
    reference.md     # full reference - loaded ON DEMAND, not by default
    ml-patterns.md   # ML pipeline task templates - loaded ON DEMAND
resources/
  template-minimal/  # the project scaffold init-project copies into a new project
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
- **Be token-efficient - you MUST.** Every word in always-loaded text (`SKILL.md`)
  is re-paid on every activation. Write like an expert prompt engineer: say it
  once, in the fewest words that still land. The full "why" goes in
  `design-notes.md` (never loaded at runtime). A rule that gets *longer* under
  edit is a smell - tighten it or push the depth down a tier. (E.g. a good rule is
  usually just imperative + the rationalization it blocks + one reason - but treat
  that as a sample of the style, not a required template.)
- When you change skill behavior, update `docs/design/design-notes.md` if the *rationale*
  changed, and `docs/CHANGELOG.md` always.

## Develop / test loop

```
claude --plugin-dir D:\OneDrive\dev\oryxlib\oryxflow-claude-plugin   # load without installing
/reload-plugins                                              # after each edit
/plugin validate .                                           # check both manifests
git config core.hooksPath .githooks                          # ONE-TIME: enable repo hooks
```

`/plugin validate .` (or `claude plugin validate .`) checks `plugin.json` and
`marketplace.json`. Run it before committing manifest changes.

`git config core.hooksPath .githooks` (one-time per clone) enables the versioned
pre-commit hook in `.githooks/`, which enforces that the scaffold floor baseline
matches in its two homes (the template stamp and `SKILL.md`) - see the Release
section and the architecture playbook. The hook only guards that the two AGREE;
deciding a floor change is migration-worthy (and bumping the baseline) is still
yours.

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
   `/plugin marketplace update oryxflow`.

The changelog's top version and `plugin.json` `version` must always match. If
`version` is omitted, git installs pin to the commit SHA (every commit is a new
version). We set an explicit version, so it MUST be bumped for updates to
propagate cleanly.

## Source-of-truth notes

The skill also still exists at `~/.claude/skills/oryxflow` (the pre-plugin copy).
This repo is becoming canonical. Avoid editing both - once the plugin is
verified, delete the `~/.claude/skills/oryxflow` copy so they cannot drift.

`resources/template-minimal/` is the project scaffold that `init-project` copies
into a new project. Edit it directly here - this repo is canonical for it. It
ships the project wiring (`tasks.py`, `flow.py`, `run.py`, `cfg.py`,
`flow_params.py`, `visualize.py`, `viz-template.ipynb`), the project `CLAUDE.md`,
`docs/oryxflow-data.md`, `.creds.yaml.example`, an `eda/` package root, and the
`data/`, `reports/`, and `reports/render/` dirs. Those three dirs are kept by a
`.gitkeep` that must be FORCE-added (`git add -f`): they match the `.gitignore`
`.*` dotfile rule, so a plain `git add` skips them. `tasks.py` / `flow_params.py`
ship the intentional `PLACEHOLDER SCAFFOLD` markers (leave them). Bump the plugin
version after any scaffold change so installs pick it up.

## Git

- Commit messages: imperative summary line; end with the Co-Authored-By trailer.
- Default branch is `main` (tracks `origin/main` on GitLab). Do not use `master`.
- Commit-message tool gotcha: PowerShell here-string syntax (`@'...'@`) is NOT a
  here-string in the Bash tool - the `@` chars get passed literally into the
  message (e.g. a subject like `@ Rename ...`). For multi-paragraph messages,
  use repeated `-m` flags with normal quoted strings in the Bash tool, or use
  the `@'...'@` here-string only in the PowerShell tool. Don't mix the two.

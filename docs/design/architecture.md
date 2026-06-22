# Architecture - the d6tflow plugin

The map to read FIRST when changing this repo - so you can edit the right file
without exploring. This doc is a map; it does NOT restate the operative files,
it points to them:

- `skills/d6tflow/SKILL.md` - the skill's runtime behavior (the spec).
- root `CLAUDE.md` - how to develop/release the plugin (dev loop, conventions).
- `README.md` - install + how an end user uses it.
- `docs/design/design-notes.md` - WHY each non-obvious decision was made (read
  before reversing one).

## What this is (one paragraph)

A single-skill Claude Code plugin for working in d6tflow data-science projects
(d6tflow = a data-pipeline library). It ships the `d6tflow` skill (model-
activated guidance) and two manual commands - `/d6tflow:init-project` (scaffold a
new project) and `/d6tflow:init-gitlfs` (put `data/` under Git LFS). The repo is
also its own marketplace, so it installs directly from git or a local path.

## Two interacting artifacts

Keep these straight - changes go to different places:

1. **This repo (the plugin)** - ships the skill, the commands, and the project
   scaffold at `resources/template-minimal/`. The scaffold is edited directly
   here; this repo is canonical for it.
2. **The installed `d6tflow` library** (pip) - the framework user projects run on.
   Not shipped here; the skill documents how to use it. This repo is NOT a place
   to run d6tflow (there is no pipeline here).

## Components (this repo)

| Path | Responsibility | Load tier |
|------|----------------|-----------|
| `.claude-plugin/plugin.json` | manifest; `version` is date-based `YY.M.D` | - |
| `.claude-plugin/marketplace.json` | self-marketplace entry | - |
| `skills/d6tflow/SKILL.md` | runtime behavior + essentials; frontmatter `description` drives activation | on activation |
| `skills/d6tflow/reference.md` | full library reference (task types, patterns) | on demand |
| `skills/d6tflow/ml-patterns.md` | ML task templates (features, training, SHAP, backtest) | on demand |
| `commands/init-project.md` | `/d6tflow:init-project`; manual (`disable-model-invocation: true`) | on invoke |
| `commands/init-gitlfs.md` | `/d6tflow:init-gitlfs`; manual (`disable-model-invocation: true`) | on invoke |
| `resources/template-minimal/` | project scaffold (edited directly here) | copied by init |
| `docs/design/architecture.md` | this map | dev-time |
| `docs/design/design-notes.md` | rationale (WHY) | dev-time |
| `docs/CHANGELOG.md` | change history | dev-time |
| root `CLAUDE.md` | dev loop, conventions, release, source-of-truth | always (dev sessions) |
| `README.md` | install + usage | - |

## Load tiers (the cost model that shapes everything)

- **Always loaded**: the project's own `CLAUDE.md` (in a USER project); the root
  `CLAUDE.md` (in THIS repo). Keep lean.
- **On skill activation**: `SKILL.md`.
- **On demand**: `reference.md`, `ml-patterns.md`.

Every line in an always/activation file is paid for on each load. This is why
`SKILL.md` stays essentials-only and depth lives in the on-demand files (two-tier
split), and why the architecture/playbook lives here, not in `CLAUDE.md`.

## Control & data flows

### Scaffold a new project - `/d6tflow:init-project`

```
command body -> reads ${CLAUDE_PLUGIN_ROOT}/resources/template-minimal/
             -> SHELL copy (robocopy / cp -n, skip-existing, never overwrite)
             -> ${CLAUDE_PROJECT_DIR}; then creates data/
```
Pre-flight refuses to clobber an existing project. The copy is a shell command,
never an LLM read+write (slow; would corrupt `visualize.ipynb`). Commands get a
reliable `${CLAUDE_PLUGIN_ROOT}`; skills do not - that is why init is a command.

### Put data under Git LFS - `/d6tflow:init-gitlfs`

```
command body -> checks git-lfs binary + filters (git lfs install)
             -> ensures a git repo on main (git init -b main)
             -> comments the data-files block in .gitignore (un-ignore)
             -> git lfs track "data/**" -> commits .gitattributes + .gitignore
```
A separate manual command (not part of init-project) because LFS is opt-in: most
scaffolds never commit `data/`. Un-ignoring before `git lfs track` is deliberate -
data ignored or added before tracking would bypass LFS.

### Activate + orient (the skill)

The skill auto-activates when working in a d6tflow project (or `/d6tflow:d6tflow`).
It orients from what the project already documents, instead of re-scanning:
- **pipeline meaning is in the code**: `tasks.py` module docstring (goal) + per-
  task docstrings + `@d6tflow.requires(...)` (the DAG; `flow.preview()` summarizes
  it) + `flow_params.py` comments.
- **data findings** live in `docs/d6tflow-data.md` (the one fact set with no code
  home).
Default invocation is lightweight; deep exploration (profiling data, writing the
data doc) is opt-in (`/d6tflow:d6tflow explore` or a plain-language request).

## Invariants (do NOT break)

| Invariant | Why / enforced where |
|-----------|----------------------|
| ASCII only in all files | Windows safety; `CLAUDE.md` conventions |
| Keep `SKILL.md` lean; depth -> `reference.md` / `ml-patterns.md` | load-tier cost; design-notes "two-tier" |
| In-code-first docs: pipeline meaning in docstrings, only data findings in a file | avoid duplication/drift; design-notes "in-code-first" |
| One `PLACEHOLDER` marker = "not real yet" across code AND the data doc | uniform signal; design-notes "PLACEHOLDER marker" |
| `init-project` copies via shell, never LLM read+write | speed + notebook integrity |
| No inline python / no `python -c` in user projects | skill rule (use `eda/<name>.py`) |
| `version` is `YY.M.D`; bump on any change installed copies should get | `CLAUDE.md` release section |

## Where to change X (playbook)

| To change... | Edit... | Then... |
|--------------|---------|---------|
| Skill runtime behavior / orientation logic | `skills/d6tflow/SKILL.md` | `/reload-plugins` (dev) |
| What auto-activates the skill | `SKILL.md` frontmatter `description` | - |
| Task-type table / deep patterns / debugging | `skills/d6tflow/reference.md` | - |
| ML pipeline templates | `skills/d6tflow/ml-patterns.md` | - |
| Any scaffold/template file (wiring, `CLAUDE.md`, data doc, `.gitignore`) | `resources/template-minimal/` directly | bump version |
| Scaffold copy behavior / pre-flight | `commands/init-project.md` | - |
| Git LFS init steps (install check, track, commit) | `commands/init-gitlfs.md` | - |
| The conventions floor a new project ships with | `resources/template-minimal/CLAUDE.md` (+ source repo) | - |
| Cut a release | `plugin.json` `version` (`YY.M.D`) + add `docs/CHANGELOG.md` entry | commit (+ push if git-installed) |
| Record a design decision | `docs/design/design-notes.md` (and this map if structure changed) | - |

## Release & propagation

Short version: `--plugin-dir` + `/reload-plugins` for the dev loop (reads files
live, no bump). An *installed* copy (git or local-clone marketplace) only picks up
changes after a `version` bump + commit + `/plugin marketplace update d6tflow`.
Full detail: root `CLAUDE.md` and README "How edits propagate".

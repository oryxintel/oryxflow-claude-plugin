# Architecture - the oryxflow plugin

The map to read FIRST when changing this repo - so you can edit the right file
without exploring. This doc is a map; it does NOT restate the operative files,
it points to them:

- `skills/oryxflow/SKILL.md` - the skill's runtime behavior (the spec).
- root `CLAUDE.md` - how to develop/release the plugin (dev loop, conventions).
- `README.md` - install + how an end user uses it.
- `docs/design/design-notes.md` - WHY each non-obvious decision was made (read
  before reversing one).

## What this is (one paragraph)

A single-skill Claude Code plugin for working in oryxflow data-science projects
(oryxflow = a data-pipeline library). It ships the `oryxflow` skill (model-
activated guidance) and four manual commands - `/oryxflow:init-project` (scaffold
a new project), `/oryxflow:init-gitlfs` (put `data/` under Git LFS),
`/oryxflow:update-project` (reconcile an old project's scaffold floor to the latest
template), and `/oryxflow:check-standards` (check code against the house standards -
naming, style, docstrings). The repo is also its own marketplace, so it installs
directly from git or a local path.

## Two interacting artifacts

Keep these straight - changes go to different places:

1. **This repo (the plugin)** - ships the skill, the commands, and the project
   scaffold at `resources/template-minimal/`. The scaffold is edited directly
   here; this repo is canonical for it.
2. **The installed `oryxflow` library** (pip) - the framework user projects run on.
   Not shipped here; the skill documents how to use it. This repo is NOT a place
   to run oryxflow (there is no pipeline here).

## Components (this repo)

| Path | Responsibility | Load tier |
|------|----------------|-----------|
| `.claude-plugin/plugin.json` | manifest; `version` is date-based `YY.M.D` | - |
| `.claude-plugin/marketplace.json` | self-marketplace entry | - |
| `skills/oryxflow/SKILL.md` | runtime behavior + essentials; frontmatter `description` drives activation | on activation |
| `skills/oryxflow/reference.md` | full library reference (task types, patterns, silent-data-error guards) | on demand |
| `skills/oryxflow/conventions.md` | house conventions (project layout, code-org-by-subject, naming columns/tasks/vars, scaling a growing project) | on demand |
| `skills/oryxflow/ml-patterns.md` | ML task templates (features, training, SHAP, backtest) + prod lifecycle | on demand |
| `commands/init-project.md` | `/oryxflow:init-project`; manual (`disable-model-invocation: true`) | on invoke |
| `commands/init-gitlfs.md` | `/oryxflow:init-gitlfs`; manual (`disable-model-invocation: true`) | on invoke |
| `commands/update-project.md` | `/oryxflow:update-project`; reconcile old project floor to latest scaffold; manual | on invoke |
| `commands/check-standards.md` | `/oryxflow:check-standards`; check code against the house standards (naming, style, docstrings); manual. Points AT `conventions.md`/`SKILL.md` for the rules (does not restate them) | on invoke |
| `resources/template-minimal/` | project scaffold (edited directly here) | copied by init |
| `resources/template-prod/` | graduated run-tier add-ons (`run_prod.py`, `run_eda.py`); NOT copied by init - copied by hand when a project needs prod / comparison tiers | on graduation |
| `docs/design/architecture.md` | this map | dev-time |
| `docs/design/design-notes.md` | rationale (WHY) | dev-time |
| `docs/CHANGELOG.md` | change history | dev-time |
| root `CLAUDE.md` | dev loop, conventions, release, source-of-truth | always (dev sessions) |
| `README.md` | install + usage | - |

## Load tiers (the cost model that shapes everything)

- **Always loaded**: the project's own `CLAUDE.md` (in a USER project); the root
  `CLAUDE.md` (in THIS repo). Keep lean.
- **On skill activation**: `SKILL.md`.
- **On demand**: `reference.md`, `conventions.md`, `ml-patterns.md`.

Every line in an always/activation file is paid for on each load. This is why
`SKILL.md` stays essentials-only and depth lives in the on-demand files (now
three: `reference.md` = library API, `conventions.md` = house style for layout /
code-org / naming, `ml-patterns.md` = ML templates), and why the
architecture/playbook lives here, not in `CLAUDE.md`.

## Control & data flows

### Scaffold a new project - `/oryxflow:init-project`

```
command body -> reads ${CLAUDE_PLUGIN_ROOT}/resources/template-minimal/
             -> SHELL copy (robocopy / cp -n, skip-existing, never overwrite)
             -> ${CLAUDE_PROJECT_DIR}; then creates data/
```
Pre-flight refuses to clobber an existing project. The copy is a shell command,
never an LLM read+write (slow; would corrupt `viz-template.ipynb`). Commands get a
reliable `${CLAUDE_PLUGIN_ROOT}`; skills do not - that is why init is a command.

### Put data under Git LFS - `/oryxflow:init-gitlfs`

```
command body -> checks git-lfs binary + filters (git lfs install)
             -> ensures a git repo on main (git init -b main)
             -> comments the data-files block in .gitignore (un-ignore)
             -> git lfs track "data/**"           (one call)
             -> git lfs track "reports/render/**"  (a second call)
             -> commits .gitattributes + .gitignore
```
A separate manual command (not part of init-project) because LFS is opt-in: most
scaffolds never commit `data/`. Un-ignoring before `git lfs track` is deliberate -
data ignored or added before tracking would bypass LFS.

### Activate + orient (the skill)

The skill auto-activates when working in a oryxflow project (or `/oryxflow:oryxflow`).
It orients from what the project already documents, instead of re-scanning:
- **pipeline meaning is in the code**: `tasks.py` module docstring (goal) + per-
  task docstrings + `@oryxflow.requires(...)` (the DAG; `flow.preview()` summarizes
  it) + `flow_params.py` comments.
- **data findings** live in `docs/oryxflow-data.md` (the one fact set with no code
  home).
Default invocation is lightweight; deep exploration (profiling data, writing the
data doc) is opt-in (`/oryxflow:oryxflow explore` or a plain-language request).

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
| Skill runtime behavior / orientation logic | `skills/oryxflow/SKILL.md` | `/reload-plugins` (dev) |
| What auto-activates the skill | `SKILL.md` frontmatter `description` | - |
| Task-type table / deep patterns / debugging / silent-data-error guards | `skills/oryxflow/reference.md` | - |
| Project layout / code-org-by-subject / naming (column, task, df) | `skills/oryxflow/conventions.md` | - |
| Scaling LAYOUT (graduated `tasks.py` split, spine, axes, app) | `skills/oryxflow/conventions.md` "Scaling up" | - |
| ML pipeline templates | `skills/oryxflow/ml-patterns.md` | - |
| PROD lifecycle (`params_prod`, `RunAll...Prod`, selective resets, notebook->pipeline) | `skills/oryxflow/ml-patterns.md` "Productionizing" | - |
| Any scaffold/template file (wiring, `CLAUDE.md`, data doc, `.gitignore`) | `resources/template-minimal/` directly | bump version + floor stamp (next row) |
| A graduated run-tier file (`run_prod.py`, `run_eda.py`) | `resources/template-prod/` directly + guidance in `conventions.md` "Run tiers by lifecycle" | NOT copied by init / not a floor file; changelog bullet only |
| A reconcile-by-default FLOOR file (`CLAUDE.md`, `viz-template.ipynb`) | the template file, AND bump the floor baseline to the new version in BOTH the template `CLAUDE.md` `<!-- oryxflow-floor: VERSION -->` stamp and `SKILL.md`'s comparison value | the two must stay equal (the `.githooks/pre-commit` check blocks a commit if they differ) - the skill nudges a project stale when its stamp < SKILL's value |
| A low-churn floor file (`.gitignore` - owned by `init-gitlfs` - or `.creds.yaml.example`) | the template file only | `update-project` treats these as additive / on-demand; a baseline bump is optional (low staleness value) |
| Scaffold copy behavior / pre-flight | `commands/init-project.md` | - |
| Reconcile an OLD project's floor to the latest scaffold | `commands/update-project.md` | - |
| Git LFS init steps (install check, track, commit) | `commands/init-gitlfs.md` | - |
| A naming, code-STYLE, or docstring RULE the checker enforces | `conventions.md` / `SKILL.md` ONLY - the rule has ONE home; `check-standards.md` points at these by section name and must NOT restate the rule | if you RENAME a section, update the pointer in `commands/check-standards.md` (steps 1 + 3); a NEW dimension (not a new rule) adds one bullet to `check-standards.md` step 3 |
| The conventions floor a new project ships with | `resources/template-minimal/CLAUDE.md` (+ source repo) | - |
| Cut a release | `plugin.json` `version` (`YY.M.D`) + add `docs/CHANGELOG.md` entry | commit (+ push if git-installed) |
| Record a design decision | `docs/design/design-notes.md` (and this map if structure changed) | - |

## Release & propagation

Short version: `--plugin-dir` + `/reload-plugins` for the dev loop (reads files
live, no bump). An *installed* copy (git or local-clone marketplace) only picks up
changes after a `version` bump + commit + `/plugin marketplace update oryxflow`.
Full detail: root `CLAUDE.md` and README "How edits propagate".

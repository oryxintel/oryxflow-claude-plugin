---
description: Bring an existing oryxflow project's scaffold floor up to date with the latest bundled template - diff the floor files (CLAUDE.md, .gitignore, viz-template.ipynb, docs skeleton) against the current template, propose a migration plan, and apply it only after the user confirms. Never touches the user's pipeline files.
disable-model-invocation: true
---

# Update a oryxflow project to the latest scaffold

A project scaffolded by `/oryxflow:init-project` a while ago can drift from the
current template: missing conventions in `CLAUDE.md`, an older `.gitignore`, a
stale `viz-template.ipynb`, etc. This command brings the project's SCAFFOLD FLOOR
up to date WITHOUT clobbering the real pipeline the user has built on top of it.
It is the maintenance counterpart to `/oryxflow:init-project` (which bootstraps and
deliberately refuses to overwrite an existing project).

- Template (source of truth): `${CLAUDE_PLUGIN_ROOT}/resources/template-minimal/`
- Target: the current project `${CLAUDE_PROJECT_DIR}`.

There is no version stamp to diff against - you reconcile by reading both sides
and judging what changed. So this is a PLAN-then-APPLY command: you author a
migration plan from the plugin's own guidance, show it, and edit only on the
user's go-ahead.

## 1. Load the oryxflow skill first

The plugin's `oryxflow` skill is what lets you tell scaffold FLOOR (plugin-owned,
safe to update) from PROJECT content (user-owned, never clobber). If it is not
already active, load it now. If the plugin is not available at all, STOP and tell
the user - this command needs it.

## 2. Categorize every template file

Walk `${CLAUDE_PLUGIN_ROOT}/resources/template-minimal/` and sort each file into
one of three buckets. This split is the whole point - get it right before
proposing anything.

- **FLOOR (reconcile by default).** Files the plugin owns AND that actually
  evolve; the project should track the template. These carry conventions, not
  pipeline logic:
  - `CLAUDE.md` - the portable floor and the usual reason to run this; it carries
    the conventions AND the `<!-- oryxflow-floor: VERSION -->` stamp.
  - `viz-template.ipynb` - the report template (copies the user made,
    `viz-<topic>.ipynb`, are project content - leave them).
- **LOW-CHURN (additive / on demand only).** Floor files that almost never change
  upstream, or that another command owns. Do NOT proactively reconcile these;
  act only if the user asks OR the template genuinely ADDED something, and then
  only additively - never rewrite:
  - `.gitignore` - rarely changes, and `/oryxflow:init-gitlfs` deliberately edits
    it (comments out the `# <data files>` block, may add project ignores). Never
    re-enable that block or drop project-added entries; at most append a brand-new
    ignore pattern the template introduced.
  - `.creds.yaml.example` - rarely if ever changes; touch only on request, or if
    the template added an example key.
- **SKELETON (reconcile structure only).** Files that ship as a placeholder and
  then get filled in. Update headers / structure / markers that changed in the
  template, but keep all real content the user has written:
  - `docs/oryxflow-data.md` (ships with a `PLACEHOLDER` line; if the project has
    filled it, only reconcile structure, never overwrite findings).
- **PROJECT (do NOT touch).** Wiring the user edits to build their pipeline.
  Report template-vs-project structural differences as NOTES only; never rewrite:
  - `tasks.py`, `flow_params.py` (ship with `PLACEHOLDER SCAFFOLD` markers the
    user has since replaced), `cfg.py`, `flow.py`, `run.py`, `visualize.py`.
  - Any file absent from the template but present in the project.

If a FLOOR file is MISSING from the project entirely, propose adding it verbatim.

The `CLAUDE.md` floor stamp (`<!-- oryxflow-floor: VERSION -->`) is what the skill
reads to detect staleness. Part of this migration is setting the project's stamp
to match the template's current value (add it if the old `CLAUDE.md` has none).

## 3. Diff and build the migration plan

For each FLOOR and SKELETON file (and any LOW-CHURN file the user asked about, or
that the template actually added to), compare the template version against the
project's and produce a concrete, section-level plan:

- What the template ADDS that the project lacks (e.g. the "check the `oryxflow`
  skill is available" block in `CLAUDE.md`) - these are the migrations.
- What the template CHANGED that the project still has in the old form.
- What the project has that the template does not - PRESERVE it; assume it is an
  intentional project customization, not drift. Call it out so the user can
  confirm.

Do the comparison by reading files, not by blind overwrite. The merge must keep
project-specific edits to FLOOR files (a team may have tuned `CLAUDE.md`).

## 4. Propose, then apply

Present the plan as a per-file summary: for each file, the sections you will add,
the lines you will update, and anything you are deliberately preserving or
leaving as a note. Do NOT edit yet.

Wait for the user's confirmation. They may accept all, accept per-file, or skip
items. Apply only what they approve, with `Edit` (surgical, preserving
surrounding content) for files that already exist and `Write`/copy for FLOOR
files being added fresh. Re-state the no-clobber rule to yourself: never replace a
PROJECT-bucket file, and never drop project content from a FLOOR file.

## 5. Report

List what was UPDATED (file + sections), what was ADDED, what was PRESERVED as a
deliberate project customization, and any PROJECT-bucket structural differences
you noted but did not touch. State the floor stamp the project now carries. If
`CLAUDE.md` gained the skill-availability check, point out that future sessions
will now remind the user to load the plugin.

Also NOTE (do not act) whether the project has DISABLED auto invalidation: on
`oryxflow >= 26.7.12` code-edit reruns are automatic by default, so an ordinary
project is protected with no per-task work. But if `settings.code_version_auto =
False` is set (grep `cfg.py` / the run wiring), the project is on the pre-auto
opt-in discipline - a code edit rides on manual `reset` or an explicit
`code_version` - so flag it as a recommendation to either re-enable auto or keep
locking tasks deliberately. This is NOT part of the scaffold reconcile (it touches
PROJECT-bucket wiring, which this command never edits), so surface it only; do not
change it unless the user asks.

# Design notes - why the d6tflow skill is shaped this way

Rationale behind non-obvious decisions, so future edits do not undo them by
accident. Update this when the *reasoning* changes, not just the text.

## Two-tier content: SKILL.md vs reference.md

`SKILL.md` loads into context every time the skill activates; `reference.md` does
not. So `SKILL.md` carries only the essentials an agent needs on every task, and
everything deep (task-type tables, advanced patterns, recipes, the full
project-structure walkthrough) lives in `reference.md`, pulled in on demand.

Keeping `SKILL.md` lean is a recurring cost decision: every line is paid for on
each activation. Resist moving reference material up into it.

## The skill orients from code + a data doc, not by re-scanning

A d6tflow project documents itself in two places, and the skill reads and trusts
them instead of re-deriving structure by scanning every file each session:

- **The pipeline is in the code**: the `tasks.py` module docstring (goal), per-
  task docstrings (what each does), `@d6tflow.requires(...)` decorators (the DAG;
  `flow.preview()` summarizes it), and parameter comments in `flow_params.py`.
- **`docs/d6tflow-data.md`**: the data (sources, schema, quirks, rules) - the one
  fact set with no code home. A larger project may split it into more
  `docs/d6tflow-data*.md` files (the flat `d6tflow-` prefix was chosen over a
  `docs/d6tflow/` subfolder to keep nesting shallow).

Why in-code-first: per-task meaning belongs next to the code it describes (it
cannot drift, and it is idiomatic Python). A separate pipeline doc would just
duplicate the docstrings and the `@requires` graph and rot. Only data findings -
which describe external data and accumulate over time - have no code home, so
only they get a file. See "Three-layer model" below for the full rationale.

Why orient from these at all: without them, every session re-explored the whole
project (reading all `.py`, listing `data/`, etc.) to rediscover what was known.

Implication: keeping docstrings and the data doc current is part of "done" for
any change. A change that does not makes the next session pay the scan cost again.

## Default invocation is lightweight; deep exploration is opt-in

A plain activation orients cheaply (read docs if present; otherwise classify the
project) and then stops. It does NOT auto-inspect `data/`, read raw sources,
write `eda/` scripts, or build the docs.

Why: that exploration is expensive and is the user's call to start. It runs only
on `/d6tflow explore` or a plain-language request to orient/explore/inspect. The
trigger surface is documented in `SKILL.md` so it stays discoverable.

## One uniform PLACEHOLDER marker (code AND docs)

Scaffold `.py` files ship present and runnable (you cannot `from flow import
flow` from nothing, and the wiring is the thing worth demonstrating). To stop a
present file from being mistaken for real work, the placeholder LOGIC carries a
marker comment directly above it: `# PLACEHOLDER SCAFFOLD - ...`. The marker sits
on the task/params, not above the imports, because the imports are real code.

The marker carries over to the rest of the scaffold: the `tasks.py` module and
task docstrings ship as placeholders, and `/d6tflow:project-init` ships
`docs/d6tflow-data.md` as a short skeleton with a `PLACEHOLDER` HTML comment on
line 1. Filling any of them means writing real content and deleting the marker.

So there is ONE rule across the whole project: a `PLACEHOLDER` marker means "not
real yet - replace it, do not trust it." Nothing marked anywhere = a real,
captured project.

History: an earlier design used doc *absence* as the "not captured" signal (docs
were not pre-created), which inverted the code signal (present+marked) against
the docs signal (absent). That asymmetry was a wart. Using one marker everywhere
- including the placeholder docstrings - unifies the rule and lets the skeleton
live in the file the agent actually fills (no inline template needed in SKILL.md).

## Fresh-scaffold report is onboarding, not a description of the guts

When classifying a fresh scaffold, the obvious move - "report the state" - leads
the agent to describe the placeholder logic it just read (dummy `range(10)`,
"Process doubles it"). That is a leak: those internals are throwaway wiring, not
project facts, and narrating them reads as if the project does something real.

So the lightweight report is split by state. A built pipeline gets summarized; a
fresh scaffold gets *onboarding* - a short welcome plus how to create tasks, load
data, and run the flow, then the two opt-in next steps. The placeholder guts are
explicitly off-limits to narrate. Keep this distinction if the report text is
ever reworked: the scaffold case is about getting the user started, not about
faithfully reporting what the scaffold contains.

## data/ holds two different things

Raw source inputs are typically loose files directly under `data/` (`.csv`,
`.xlsx`, etc.). d6tflow task OUTPUTS are parquet written into per-task subfolders
(`data/GetData/*.parquet`). When hunting for inputs, ignore the parquet
subfolders. The source path can be redirected via `cfg.py`.

## Three-layer model: plugin / project docs / always-on CLAUDE.md

Where each kind of information lives, and why:

- **Generic d6tflow knowledge** (task types, patterns, ML recipes, conventions)
  lives ONLY in the plugin: `SKILL.md` (essentials), `reference.md` (depth),
  `ml-patterns.md` (ML, on demand). It is identical across projects, so it must
  not be copied into each one. Plugin-izing this is the whole point - it ends the
  old habit of dumping a `claude-d6tflow.md` guide into every repo.
- **Project-specific truth** lives with the thing it describes: pipeline meaning
  in the code's docstrings, data findings in `docs/d6tflow-data.md`. Unique per
  project, evolves with the code; this is what lets the skill skip re-scanning.
  In-code-first is deliberate - documentation that can sit next to its code
  should, so it cannot drift; a file is used only for what has no code home.
- **The bootstrap/link** is the project's always-loaded `CLAUDE.md`. It declares
  "this is a d6tflow project," points to the code + data doc, and restates the
  conventions floor (ASCII, eda/ not inline python, no try/except, flow-file
  discipline, trust auto file mgmt) so they hold even with the plugin NOT
  installed. The plugin holds the depth; `CLAUDE.md` holds the wiring + floor.

This earlier was an open question (the template once shipped a rich generic guide
and a detailed data-doc skeleton at those doc paths, which collided with the
"absence = explore" signal and duplicated plugin knowledge). Resolution: generic
content is the plugin's job (harvested into `reference.md` / `ml-patterns.md` and
deleted from the project); pipeline meaning is in-code; and only the data doc
ships as a marked PLACEHOLDER skeleton (see the marker note above).

## Scaffolding: the init command and the vendored template

A new project is created by the `/d6tflow:project-init` slash command (commands
get a reliable `${CLAUDE_PLUGIN_ROOT}`; skills do not, so init is a command, not
the skill). It copies the bundled template into the user's cwd with a SHELL copy
(robocopy / cp -n), skip-existing / never-overwrite, and never reads+rewrites
files via the LLM (which would be slow and could corrupt `visualize.ipynb`).

The template lives at `resources/template-minimal/`. It is a **vendored mirror**
of the separate `d6tflow-template-minimal` repo (the source of truth) - kept
unpacked (not zipped) so template changes are diffable in PRs and copying needs
no archive tooling. Do not hand-edit the mirror; re-sync it from the source repo.
The provenance/sync note lives in the plugin's top-level `CLAUDE.md`, not as a
file inside the template (which would just have to be excluded from every copy).

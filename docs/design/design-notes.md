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

## Code organization scales by subject (eda / utils / viz)

The flat starter (`tasks.py` + `visualize.py` + ad-hoc `eda/`) stops scaling once
a project has many tasks and reusable helpers/plots. The convention groups
supporting code by the SUBJECT it concerns (a task or a dataset), mirroring how
the pipeline is keyed on tasks - so a task's probes, helpers, and figures are
found by name, the same way the cache is keyed by task.

The forks that were decided (each had a defensible alternative):

- **Group by task OR dataset, not a `_reference/` bucket.** Non-task reference
  data still has a natural subject - the dataset - so `eda/<dataset>/` keeps ONE
  grouping axis instead of adding a parallel bucket taxonomy.
- **Build-a-data-input code prefers becoming a real source task** (hybrid): if it
  produces a `data/` input, the DAG should own and cache it; only true one-offs
  stay as dataset-folder scripts.
- **snake_case modules (PEP 8), not task-name CamelCase.** Idiomatic import paths;
  the cost is a mechanical CamelCase->snake mapping. (CamelCase-matching was the
  runner-up - a literal `{taskname}` file - but PEP 8 won.)
- **Filenames name the specific check, never a bare verb.** The folder supplies
  the subject, so `verify.py` would discard the one bit of information the
  filename can carry; `verify_wages.py` reads with the folder as "verify wages of
  <subject>".
- **Shared helpers default to a concept/dataset module (concept-by-default).** A
  helper used by 2+ subjects goes in a module named for the shared idea
  (`utils/geo.py`); a single subject's extracted helper in `utils/<subject>.py`;
  truly generic in `__init__.py`. This was reached EMPIRICALLY. An earlier draft
  decided the home from DAG topology (chain -> the upstream task's module, siblings
  -> a concept module). A trial on a real, complex project found the chain branch
  had ZERO instances - every shared helper was siblings -> concept - so topology
  added cognitive cost (and a diamond-misread risk) without ever changing the
  answer. Concept-by-default gives the identical result with no topology reasoning;
  a rare no-natural-concept helper may fall back to the upstream producer's module.
  Also rejected: `__init__.py`-by-default (reuse != general; junk drawer +
  move-churn when the 2nd user appears) and task-of-first-use (historical,
  brittle).
- **Extract on the 2nd use** (or when a single-use helper is large), not
  preemptively - avoids a swarm of near-empty per-task modules.
- **`eda/` is read-only; builders are separate.** A probe asserts, it does not
  write `data/`. Loading external data is just the loader-task pattern, so it is a
  source task BY DEFAULT (DAG + cache). Two cases stay a `utils/<dataset>.py`
  script instead: hand-curated data (not reproducible, so calling it a "task" is
  misleading) and output a d6tflow task type cannot store (not a DataFrame or a
  serializable object - a raw file asset / directory, where a task buys little).
  Surfaced by the real project, where in-place csv cleaners had no honest home as
  either probe or task.
- **snake_case is author-declared, not algorithmic.** Case-boundary splitting
  cannot recover a glued-lowercase word (`EmploymentbyMSA` -> `employment_by_msa`),
  so a `# task: <ClassName>` header in the subject module is the source of truth;
  the split rule is only a default. Shipping a name dictionary was considered and
  rejected as overkill for hand-authored modules.
- **viz is not a special eda subject.** Probes/tests for `viz/` code group under
  the subject the figure is about (`eda/<subject>/`), like any other probe - there
  is no `eda/viz/` carve-out. eda includes viz.

Implication: `eda/` probes are now nested (`eda/<subject>/<name>.py`, run
`python -m eda.<subject>.<name>`, each folder an `__init__.py`), updating the
older flat `python -m eda.<name>` form.

## Importing notebooks stay at the project root

A notebook that imports the pipeline (`from flow import flow`) must run with cwd =
the project root - the same root-cwd invariant the whole project relies on (`data/`
and `.creds.yaml` are relative). `nbconvert --execute` runs the kernel with cwd =
the notebook's OWN folder, so a notebook filed under `reports/` would break both
imports and the relative `data/` paths. Rather than patch cwd/sys.path per
notebook, importing notebooks live at the root (like `visualize.ipynb`); `reports/`
holds only the rendered HTML output (`reports/render/`). Considered and rejected: a
first-cell `os.chdir(..)` guard for `reports/*.ipynb` - it works (and fixes cwd, not
just sys.path) but adds a per-notebook idiom, where keeping the file at root needs
none.

## EDA is a learning artifact, not throwaway

The no-inline-Python rule routes probe code into `eda/` files. That is only half
the point. A probe is run to ANSWER A QUESTION about the data ("does this column
have nulls?", "which sheet holds the estimates?"), and the answer is a data
finding - the same class of fact that `docs/d6tflow-data.md` exists to hold. So
the rule pairs with a documentation duty: each `eda/` script states its question
(docstring) and makes its result legible (a clear print or a recorded comment),
and material findings get promoted into the data doc.

Why: the `eda/` file is throwaway as CODE, but the FINDING is not - it is exactly
what keeps the next session from re-deriving what was already learned (the same
"do not re-scan" payoff as orienting from code + the data doc). Framing `eda/` as
purely "throwaway" undersold this and let probe results evaporate; an uncaptured
result is a question that gets asked again. Keep the code-vs-finding distinction
if this is reworded: the script may be disposable, the knowledge is not.

Recording is NOT gated behind a confirmation. Two moments get conflated: deciding
to GO exploring (opt-in - the user's call, since it can be a big detour) versus
writing up a finding a probe has ALREADY produced (part of finishing the work).
The second is not a new decision to ask about - asking "shall I record this?"
after a data-quality finding just adds a round-trip and invites the finding to
evaporate when the user moves on. So material findings, data-quality ones
especially, get written to `docs/d6tflow-data.md` without asking.

## One uniform PLACEHOLDER marker (code AND docs)

Scaffold `.py` files ship present and runnable (you cannot `from flow import
flow` from nothing, and the wiring is the thing worth demonstrating). To stop a
present file from being mistaken for real work, the placeholder LOGIC carries a
marker comment directly above it: `# PLACEHOLDER SCAFFOLD - ...`. The marker sits
on the task/params, not above the imports, because the imports are real code.

The marker carries over to the rest of the scaffold: the `tasks.py` module and
task docstrings ship as placeholders, and `/d6tflow:init-project` ships
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

**Corollary - first-action rules belong in `CLAUDE.md`, not only `SKILL.md`.** The
skill is ACTIVATION-GATED; the project `CLAUDE.md` is ALWAYS in context. So a rule
that must govern the very first move - especially right after `/clear`, before any
skill activation - has to live in the always-loaded floor, or the model falls back
to generic instincts. The motivating failure: after `/clear`, asked to analyze a
pipeline, the model ran a shell `head` on the raw input CSV instead of
`flow.outputLoad(TheTask)` - the data ALREADY existed as that task's output, with
renamed/derived columns, so the raw input was both the wrong file and the wrong
path. The rule lands as: once a task produces the data, `outputLoad` it; do not go
back to the source to learn the output's schema. It is deliberately NOT an absolute
ban on reading raw files - that is exactly how you bootstrap a loader task for
source not yet in the pipeline (nothing to `outputLoad` yet). The distinction is
"does a task already produce this?", not the tool used. The plugin's `SKILL.md`
carries the same wording for when the skill IS active; `CLAUDE.md` catches the
cold-start case.

## Scaffolding: the init command and the template

A new project is created by the `/d6tflow:init-project` slash command (commands
get a reliable `${CLAUDE_PLUGIN_ROOT}`; skills do not, so init is a command, not
the skill). It copies the bundled template into the user's cwd with a SHELL copy
(robocopy / cp -n), skip-existing / never-overwrite, and never reads+rewrites
files via the LLM (which would be slow and could corrupt `visualize.ipynb`).

Git LFS setup is a SEPARATE command, `/d6tflow:init-gitlfs`, not folded into
init-project: LFS is opt-in (most scaffolds never commit `data/`), it mutates git
state (init, .gitignore, a commit) rather than just copying files, and it has its
own machine prerequisite (the git-lfs binary + `git lfs install` filters). The
command un-ignores the `.gitignore` data-files block BEFORE `git lfs track`,
because data that is ignored or staged before tracking bypasses LFS and then needs
`git lfs migrate` to fix. `data/**` and `reports/render/**` are LFS-tracked; the
commit is just the config (`.gitattributes` + `.gitignore`), leaving which data to
commit to the user.

The template lives at `resources/template-minimal/`, edited directly here (this
repo is canonical for it). It is kept unpacked (not zipped) so template changes
are diffable in PRs and copying needs no archive tooling.

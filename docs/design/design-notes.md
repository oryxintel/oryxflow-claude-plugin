# Design notes - why the oryxflow skill is shaped this way

Rationale behind non-obvious decisions, so future edits do not undo them by
accident. Update this when the *reasoning* changes, not just the text.

## Two-tier content: SKILL.md vs the on-demand files

`SKILL.md` loads into context every time the skill activates; the on-demand files
do not. So `SKILL.md` carries only the essentials an agent needs on every task,
and everything deep lives in files pulled in only when needed.

Keeping `SKILL.md` lean is a recurring cost decision: every line is paid for on
each activation. Resist moving reference material up into it.

### Why the on-demand depth is split three ways

The depth is NOT one file. It is `reference.md` (the oryxflow LIBRARY: task types,
params, running/reset, advanced patterns, recipes, debugging, and the silent-
data-error guards), `conventions.md` (the HOUSE STYLE: project-layout deep dive,
code-organization-by-subject, and naming columns/tasks/variables), and
`ml-patterns.md` (ML templates). The split is along a real seam - "how oryxflow
works" vs "how we organize a project" are different questions asked at different
moments. `reference.md` crossed ~1000 lines and a focused question ("where does
this code go", "how do I name this column") had to page the whole file, diluting
attention and spending context on irrelevant API material. Two on-demand files
let the agent load only the half it needs. The stopping rule is one split, not
many: each extra file adds discovery overhead and a drift surface, so depth is
cut at the load-bearing seam (library vs conventions) and no finer. Routing is in
`SKILL.md`'s header pointer and the inline pointers ("full rules in
conventions.md"); keep those accurate or the second file goes unfound.

### Why d6tflow-migration.md is an on-demand doc, not a command

The library rebrand from `d6tflow` to `oryxflow` left old projects needing a
rename. That is a rare, one-time, one-way task, so it does NOT get a slash
command (a permanent `/oryxflow:` palette entry earns its keep by being run
repeatedly; this is run once per project, if ever) and it does NOT auto-trigger
(nothing should start rewriting a user's pipeline on a plain skill load). It also
is not general library depth, so it sits OUTSIDE the reference/conventions/ml
"one split, not many" seam - it is a task playbook, discovered via a single
`SKILL.md` pointer and invoked only when the user names it. The rename itself is
mechanical (a whole-word token swap; the public API kept its shape across the
rebrand), so the doc's real work is the guardrails: plan-then-apply, flag
anything that does not map 1:1, and treat the `oryxflow` install/upgrade as a
user decision rather than installing on their behalf. And because the swap is a
quote-free ASCII token, the apply step is ONE word-boundary substitution scoped
to the grep-matched files (`.ipynb`/`.html` included) - not dozens of hand `Edit`
calls, which is what an agent defaults to and what makes the rename slow and
lossy. That is also why the doc carves the sole exception to the
no-hand-written-nbformat-JSON rule: that rule guards against corrupting cell JSON
while AUTHORING, and a whole-word token swap can't. The word `migrate` is
deliberately kept for a different feature - `/oryxflow:migrate`, which
restructures a messy notebook/script project into a pipeline (see below) - so
this rename does not claim it.

### Why /oryxflow:migrate is a command, not an on-demand doc

The counterpart decision to the one above. Restructuring an ad-hoc project into a
pipeline is a REPEATED, generative operation (run on many projects; each run
writes real code across `tasks.py` / `flow_params.py` / `cfg.py`), so unlike the
one-time `d6tflow` rename it earns a permanent `/oryxflow:` palette entry. It is
`disable-model-invocation: true` like the other write-commands - nothing should
restructure a user's code on a plain skill load; it runs only when invoked. The
command owns the MAPPING (messy anti-pattern -> oryxflow construct: linear chain
-> DAG, magic constants -> params, hardcoded paths -> `save`/`inputLoad`) and the
discipline (map-then-build, build up one task at a time so a break surfaces at its
cause, never delete the source - it is the spec and the results oracle). It does
NOT scaffold: it builds into an existing project and defers to
`/oryxflow:init-project` when there is none, keeping each command single-purpose.

### Why a "silent data errors" section exists

The library best-practices already cover validation/assertions, but the errors
that produce a WRONG NUMBER WITHOUT RAISING are a distinct class and the most
dangerous for an AI agent: an unvalidated join that multiplies rows, an assumed
column meaning, a number eyeballed off a chart, a pandas index misalignment. None
throw; all yield confident wrong analysis. They get their own section in
`reference.md` (with a SKILL.md pointer) because "make the failure loud" -
`validate=` on merges, look-before-you-conclude, quote-the-computed-number - is a
different discipline from "assert your inputs," and worth naming so it is applied.

## Off-the-shelf libraries first; a broken import is a STOP

A recurring agent failure: an `import` fails (a missing package or an ABI /
version clash - e.g. scipy dropping a symbol statsmodels' umbrella `statsmodels.api`
imports eagerly), and instead of pausing, the agent routes around it by
hand-rolling the library's work in numpy - a custom regression, AR(1), ACF. The
result is a large block of bespoke, fragile math that duplicates a standard
library: not DRY, rarely more correct, and a maintenance liability. The root
cause is two-fold, so the rule names both: (1) reach for the established library
by default, and (2) a failed import is an ENV bug to surface and fix, NOT a
license to reimplement. The behavioral half (STOP and ask before writing custom
math) is the load-bearing one, so it sits in always-loaded SKILL.md Code Style
next to the sibling "let it fail" / "STOP and ask" rules (no try/except, locked
Excel); the ML-specific depth (probe submodules on an ABI clash; the one
legitimate wrap - a documented data quirk like gap-aware lagging - and even then
validate the custom path against the library) lives in ml-patterns.md so the
always-loaded tier stays lean.

## The skill orients from code + a data doc, not by re-scanning

A oryxflow project documents itself in two places, and the skill reads and trusts
them instead of re-deriving structure by scanning every file each session:

- **The pipeline is in the code**: the `tasks.py` module docstring (goal), per-
  task docstrings (what each does), `@oryxflow.requires(...)` decorators (the DAG;
  `flow.preview()` summarizes it), and parameter comments in `flow_params.py`.
- **`docs/oryxflow-data.md`**: the data (sources, schema, quirks, rules) - the one
  fact set with no code home. A larger project may split it into more
  `docs/oryxflow-data*.md` files (the flat `oryxflow-` prefix was chosen over a
  `docs/oryxflow/` subfolder to keep nesting shallow).

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
on `/oryxflow explore` or a plain-language request to orient/explore/inspect. The
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
  misleading) and output a oryxflow task type cannot store (not a DataFrame or a
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

## Scaling a growing project: graduation, not a second template

The scaffold is flat (one `tasks.py` / `run.py` / `flow.py` / `flow_params.py`),
which is right for the ~80% of projects that stay research-only. The ~20% that
grow - mostly at the "going to prod" moment - had almost no guidance. The
question was whether to ship a second "advanced" scaffold or document a
graduation path. We chose graduation, documented across the load-tiered files,
for several reasons:

- **80/20 + restructure-as-you-grow.** Most projects never need the advanced
  shape; a second scaffold would impose its cost (more files to understand) on
  everyone or force an up-front choice the user is not equipped to make. Growing
  into structure on a concrete trigger fits how these projects actually evolve.
- **Maintenance cost of a second scaffold.** Two scaffolds drift; every wiring
  change has to land in both. One scaffold + a documented path has a single
  source of truth.

The model itself, and the forks decided:

- **Section-headers BEFORE splitting, with the headers as the cut seam.** A
  sectioned single file scales far past 500 lines (validated against a real 531-
  line / 10-task / 2-branch project that had no strain), and comment headers are
  cheap, orient the reader, and give the agent unique edit anchors. So the
  progression is naming-families -> section-headers -> split, and the split (step
  d) cuts along the section seams already drawn. Splitting on raw task count is
  explicitly wrong - hence the proactivity triggers below are file-length /
  prod / subsystem, NOT count.
- **A slim `tasks.py` spine, NOT a re-export aggregator.** When the file splits,
  `tasks.py` stays as the home of the project-goal module docstring (our
  convention mandates one, and it needs a stable home) plus the orchestration
  tasks; phase modules hold the work and import the specific sibling they depend
  on. An aggregator that re-exports every task was rejected: it invites import
  cycles and no studied real project used one (all use direct imports).
- **Two split axes: phase and subsystem.** Phase (`tasks_features/model/eval`)
  breaks up the main pipeline and imports UPSTREAM-ONLY, so the graph is acyclic
  by construction. Subsystem (an app, an LLM layer, an alt source) is just the
  existing group-by-subject rule applied to tasks - so it reuses that convention
  (subdir package when the subsystem bundles its own helpers) rather than
  inventing a parallel one.
- **`params_prod` single-source.** The prod settings live once in
  `flow_params.py` and the prod orchestration imports them. This fixes a real
  duplication seen in a studied prod project, where the prod params were re-typed
  inline in the orchestration task and could drift from the recorded set.
- **Cache-safe move is load-bearing and was VERIFIED, not assumed.** The whole
  "split later" advice rests on moving a class between modules being free. A task's
  identity is its class name: `oryxflow.core.Task.get_task_family` returns
  `cls.__name__` (no module path), confirmed empirically: the same class in two
  different modules resolves to the identical `data/<Class>/...` output path.
  RENAME still orphans the old cache (class name changed) - only MOVE is free; the
  docs keep both notes. (This is oryxflow's OWN behavior - the task base class is
  `oryxflow.core.Task`, not a luigi subclass - so it is unaffected by anything in
  luigi.)

Where it lives (load tiers): conventions.md owns the LAYOUT progression (scaling
`tasks.py`, the axes, the spine, the app); ml-patterns.md owns the PROD lifecycle
(`RunAll...Prod`, selective resets, periodic refresh, productionizing a notebook);
SKILL.md carries only the one-line pointer plus the proactive-nudge rule (trigger
+ the count-based rationalization it blocks + stay-silent-on-orient), because the
agent's behavior-shaping rule has to be in the activation-loaded file while the
depth does not.

## Importing notebooks stay at the project root

A notebook that imports the pipeline (`from flow import flow`) must run with cwd =
the project root - the same root-cwd invariant the whole project relies on (`data/`
and `.creds.yaml` are relative). `nbconvert --execute` runs the kernel with cwd =
the notebook's OWN folder, so a notebook filed under `reports/` would break both
imports and the relative `data/` paths. Rather than patch cwd/sys.path per
notebook, importing notebooks live at the root (`viz-<topic>.ipynb`); `reports/`
holds only the rendered HTML output (`reports/render/`). Considered and rejected: a
first-cell `os.chdir(..)` guard for `reports/*.ipynb` - it works (and fixes cwd, not
just sys.path) but adds a per-notebook idiom, where keeping the file at root needs
none.

The scaffold ships the report notebook as a TEMPLATE, `viz-template.ipynb`, and the
convention is one-report-per-notebook: copy the template to `viz-<topic>.ipynb`
(subject-named, like `viz/<subject>.py`) and edit the copy, never the template. The
motivating failure: a session edited the scaffold notebook in place, consuming the
template and tying one report to the generic `visualize` name. A `-template` suffix
makes "do not edit me" obvious, the copy keeps it pristine, and `--output-dir`
renders to `reports/render/viz-<topic>.html` (subject-named) for free. The copy is a
shell op, not an LLM read+write (same reason init uses a shell copy - the JSON is
binary-ish and slow/risky to rewrite); `NotebookEdit` then edits the copy's cells.

## EDA is a learning artifact, not throwaway

The no-inline-Python rule routes probe code into `eda/` files. That is only half
the point. A probe is run to ANSWER A QUESTION about the data ("does this column
have nulls?", "which sheet holds the estimates?"), and the answer is a data
finding - the same class of fact that `docs/oryxflow-data.md` exists to hold. So
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
especially, get written to `docs/oryxflow-data.md` without asking.

## One uniform PLACEHOLDER marker (code AND docs)

Scaffold `.py` files ship present and runnable (you cannot `from flow import
flow` from nothing, and the wiring is the thing worth demonstrating). To stop a
present file from being mistaken for real work, the placeholder LOGIC carries a
marker comment directly above it: `# PLACEHOLDER SCAFFOLD - ...`. The marker sits
on the task/params, not above the imports, because the imports are real code.

The marker carries over to the rest of the scaffold: the `tasks.py` module and
task docstrings ship as placeholders, and `/oryxflow:init-project` ships
`docs/oryxflow-data.md` as a short skeleton with a `PLACEHOLDER` HTML comment on
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
`.xlsx`, etc.). oryxflow task OUTPUTS are parquet written into per-task subfolders
(`data/GetData/*.parquet`). When hunting for inputs, ignore the parquet
subfolders. The source path can be redirected via `cfg.py`.

## Three-layer model: plugin / project docs / always-on CLAUDE.md

Where each kind of information lives, and why:

- **Generic oryxflow knowledge** (task types, patterns, ML recipes, conventions)
  lives ONLY in the plugin: `SKILL.md` (essentials), `reference.md` (library
  depth), `conventions.md` (house style), `ml-patterns.md` (ML), the last three on
  demand. It is identical across projects, so it must
  not be copied into each one. Plugin-izing this is the whole point - it ends the
  old habit of dumping a `claude-oryxflow.md` guide into every repo.
- **Project-specific truth** lives with the thing it describes: pipeline meaning
  in the code's docstrings, data findings in `docs/oryxflow-data.md`. Unique per
  project, evolves with the code; this is what lets the skill skip re-scanning.
  In-code-first is deliberate - documentation that can sit next to its code
  should, so it cannot drift; a file is used only for what has no code home.
- **The bootstrap/link** is the project's always-loaded `CLAUDE.md`. It declares
  "this is a oryxflow project," points to the code + data doc, and restates the
  conventions floor (ASCII, eda/ not inline python, no try/except, flow-file
  discipline, trust auto file mgmt) so they hold even with the plugin NOT
  installed. The plugin holds the depth; `CLAUDE.md` holds the wiring + floor.

This earlier was an open question (the template once shipped a rich generic guide
and a detailed data-doc skeleton at those doc paths, which collided with the
"absence = explore" signal and duplicated plugin knowledge). Resolution: generic
content is the plugin's job (harvested into `reference.md` / `conventions.md` /
`ml-patterns.md` and deleted from the project); pipeline meaning is in-code; and
only the data doc ships as a marked PLACEHOLDER skeleton (see the marker note
above).

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

## Changelogs are a diagnostic surface; a compat contract catches skew

Two readers, one artifact - the same logic as the three-layer model, applied to
change history. The agent does not browse a changelog; it CONSULTS one to diagnose
a regression after a version bump (grep the failing symbol, read from the
installed version forward, breaking-first). That only works if entries are
machine-consumable, so `docs/CHANGELOG.md` carries three load-bearing tokens -
`BREAKING:` (the grep target), a same-bullet `Migration:` clause, and backticked
symbols/commands/paths - mirroring the library's changelog. Structure IS the
machine-readability; there is no second machine format. The `.githooks/pre-commit`
lint keeps the `BREAKING:`/`Migration:` pairing from rotting.

The plugin has no API, so "breaking" is redefined: a change that makes an
*already-scaffolded* project out of date (scaffold floor, commands, enforced
conventions). Each break therefore ends in the migration action the plugin already
ships - `/oryxflow:update-project` or `/oryxflow:check-standards` - not an abstract
warning. This overlaps the floor-baseline mechanism: the migration-worthy scaffold
change is exactly the one that bumps the floor.

The **pointer must live in the skill**, not the changelog - the best changelog is
invisible without it. But the pointer is a few lines (in `reference.md`, triggered
from `SKILL.md`); changelog CONTENT is never inlined (it would re-pay context every
activation for something needed twice a year). Cross-repo links use
`raw.githubusercontent.com` (clean markdown the agent can fetch), not `blob` (HTML
chrome).

**Why a compatibility contract.** The skill instructs the agent based on LIBRARY
behavior, so a version mismatch is dangerous: the agent cannot tell a real bug from
"the skill has run ahead of the library." Stating a supported library floor (in
`SKILL.md` for no-fetch access, and authoritatively in `docs/CHANGELOG.md`) lets
the agent compare against `oryxflow.__version__` and REPORT skew instead of chasing
a phantom. Authority is split and stated: the library `CHANGELOG.md` is the source
of truth for API/behavior; when the two disagree about behavior, the library wins.
The floor is phrased as a standalone assumption ("assumes `oryxflow >= X`"), not
coupled to the plugin's own fast-moving version line, so a routine plugin release
does not falsify the sentence - only adopting new library behavior bumps it.

## Logging: two layers, log scalars / save artifacts

Domain signal, not `print`, in two layers. oryxflow already logs the lifecycle
(scheduling / completion / timing) via `oryxflow.enable_logging()` - the most useful
execution log; bracketing `flow.run()` with hand-written start/done lines (an
earlier scaffold `run.py` did this) just duplicates it. So lifecycle is oryxflow's;
in-task logging covers what it does not show - shapes, drop rates, headline
metrics, the branch taken.

Use `self.logger`, NOT a raw `from loguru import logger`. This is the load-bearing
correction (an earlier draft taught raw loguru, which is actively wrong here):
`enable_logging()` adds a handler filtered to the `oryxflow` namespace AND removes
loguru's default handler, so a raw `logger.info` from the task's own module is
SILENTLY DROPPED - the examples would have produced no output. `self.logger`
(the `Task.logger` property -> `TaskLogger`) emits from inside the oryxflow package
so it lands in that namespace and survives, and auto-tags `task_id`. Outside a task
(`run.py`) there is no `self.logger` and no clean oryxflow-namespaced logger, so
orchestration there uses `print` (verified against oryxflow source: `core.py`
`Task.logger`, `log.py` `TaskLogger` + `enable_logging`).

Knock-on simplification: because domain logs now share the ONE oryxflow sink,
`enable_logging(colorize=False)` governs color for both lifecycle and domain at
once - the earlier per-run `logger.add("run.log", colorize=False)` side-sink
workaround is gone. (`enable_logging`'s `colorize` even auto-detects: colored on a
TTY, plain when redirected - so a redirected run is grep-clean with no flag.)

Load-bearing rule: log scalars + lifecycle; SAVE rows + artifacts (frames, SHAP,
metric tables, models -> `self.save()` / xlsx), never a log line, never per-row.
A log is what you grep; a frame is what you reload. Replaced the old
`print("SUCCESS:/WARNING:/ERROR:")` prefixes (loguru stamps level + time). ASCII
still binds messages.

The reading half matters as much as the emitting half: SKILL.md "Reading the run
output" consolidates it - read the run (don't tee-and-grep), Execution Summary
first (what recomputed vs cache-hit), load artifacts for numbers (don't scrape
logs), and "no metric line" usually means wrong logger (raw loguru), not no signal.

The scaffold `run.py` surfaces this structurally: it captures `result = flow.run()`
and `print(result.summary())`, then comments the drill-down (`result.ran`/`.complete`
/`.did_run`, and `.failed`/`.failure_of` under `abort=False`). The point is to remove
the REASON to grep a finished run's log - the structured "what ran / what failed"
answer is already in captured stdout, and the object is right there to query. A bare
`flow.run()` discarded that object, which is what pushed the agent to scrape the log
for status. `WorkflowMulti.run()` returns a `MultiRunResult` that carries the same
`.summary()`/`.success`, so the one habit works for single and multi flows alike.

Tiering: SKILL.md Code Style + scaffold floor `CLAUDE.md` hold the rule;
ml-patterns.md owns the ML depth (per-stage what-to-log, the `training cutoff`
model example, the colorize switch) plus live log lines IN the `FeaturesTransform`
/ `ModelTrain` templates so the pattern is copied, not just described.

## The cache-reset gotcha is promoted to every tier (salience, not depth)

oryxflow caches on task IDENTITY (class + params), not code, so a CODE/DATA change
needs `flow.reset(Task)` (cascades downstream); a plain run reuses stale output -
the #1 oryxflow surprise. The depth already lived in `reference.md`, but that is
on-demand, so in a live session the rule was not in context when needed and a real
project's agent invented a `reset_downstream` helper instead of the built-in.

The fix was NOT to reorganize `reference.md` (its reset section is fine) but to
PROMOTE the one-liner up the tiers - same logic as the "first-action rules belong
in CLAUDE.md" corollary above: it now lives in the always-loaded floor `CLAUDE.md`
and SKILL.md's "Modify an existing task", depth + force-run alternatives still in
`reference.md`. Plus an explicit "never write a reset helper" (a helper always
means the built-in was missed), and: if a PARAMETER change is not auto-rerunning,
fix the parameter definition / inheritance, do not reset by hand. (`flow.reset`
defaults to `confirm=False` / no prompt, so it is safe in a non-interactive run as
is; `confirm=True` opts INTO the prompt.) General lesson: when an agent misses a
documented rule live, first ask whether it was in a loaded tier - promotion beats
rewriting.

## Code-aware invalidation (oryxflow >= 26.7.12): AUTO by default, lock to opt out

The engine's code-invalidation feature folded into `26.7.12` in two waves, and the
final shape is what the guidance targets. Wave one shipped the machinery
(`code_version`, an AST source-hash, `accept_code()`, `keep_versions`, the event
stream) with the hash ADVISORY-only, so correctness rode on the author remembering
to declare and bump `code_version` per tracked task. Wave two (same version)
promoted the hash to the DEFAULT AUTHORITY: `settings.code_version_auto = True`, so
a task without `code_version` derives its code identity from the AST hash of its
module + transitively imported repo-local files, and a logic edit reruns the task
and everything downstream automatically. `code_version` flipped from the primary
mechanism to an opt-in LOCK. The plugin guidance was first written for wave one
(bump-first) and then rewritten for wave two; this note records the final design
and why, so a reader who greps the changelog history is not confused by the
intermediate bump-first framing.

1. **The primary idiom is AUTO: edit -> run -> VERIFY.** No attribute to declare or
   remember; editing a task's `run()` or any helper it imports reruns the affected
   band (all parameter variants and downstream included - the old
   `runLoad(reset=True)`-per-variant sibling-staleness hazard stays retired).
   Comment/docstring/formatting edits are AST-normalized to nothing, so they never
   rerun. What auto trades the attribute-ritual for is a VERIFY-ritual, and that is
   deliberate, not incidental: auto has honest blind spots (data files, installed
   packages, dynamic dispatch, notebook-defined tasks), so the discipline the
   guidance leads with is "after an edit, confirm the edited band shows in
   `result.ran` with reason `code change (auto: <files>)`; a `ran=0` means auto did
   not see the change -> reset or lock." This is the user's core requirement - an
   agent that just edited code and sees it NOT rerun must treat that as a signal,
   not a convenient cache hit. The plentiful run/event logging exists to make the
   check cheap.

2. **The destructive-recompute risk is handled in the LIBRARY, not left to the
   agent.** Auto deletes and overwrites the old output on every rerun, so an
   output-equivalent refactor touching a slow API pull or a long backtest would
   otherwise silently discard hours of compute. The engine's answer (shipped after
   this exact concern was raised) is the expensive-recompute guard: an auto task
   whose LAST run exceeded `settings.code_version_auto_expensive_s` (default 600s)
   does not silently recompute on a code change - it stays complete and WARNS with
   the exits, so burning a long run is a decision. This is the right layer for it:
   a plugin doc telling the agent "remember to pin expensive tasks first" would be
   another memory-dependent guardrail, the very failure mode auto exists to kill;
   the guard needs no foresight. The scaffold `cfg.py` surfaces the knob
   (`code_version_auto`, `code_version_auto_expensive_s`) as commented lines so the
   opt-out is a visible choice, not a buried setting.

3. **`code_version` is the opt-out LOCK.** Declaring it tells auto to stop watching
   a task's source: the task reruns only on an explicit bump, an unbumped edit warns
   instead. With the guard covering the big destructive case automatically, the lock
   is for finer or explicit control: (a) a task you want managed by deliberate bumps
   even BELOW the guard threshold; (b) logic auto cannot hash (dynamic dispatch,
   data-driven behavior) - lock plus manual bump is the robustness path; (c) a key
   task whose cache decision you want DIFFABLE in review / `git log` (an auto rerun
   leaves no trace - the reason agent-run projects often pin headline tasks even
   though auto needs nothing). Locks toggle freely (records store token AND source
   hashes, so adding/removing on unchanged code is a no-op that never ripples). A
   locked task still reruns when an AUTO upstream changes (the fingerprint folds
   dependency fingerprints), so the lock pins only its OWN logic. Global escape
   `settings.code_version_auto = False` reverts the whole project to pure opt-in.

4. **Two mechanisms, still documented as distinct because an agent conflated them.**
   Under auto the AUTHORITY that gates completeness is the code fingerprint
   (explicit `code_version` OR the auto hash); the warn-only path now fires only for
   a LOCKED task edited without a bump. A source-inspecting agent that read only
   base `Task.complete` ("outputs exist") - which the skill itself tells agents to
   do ("installed code wins") - once wrongly concluded a code change merely warns.
   The fix stays two-tier: a library docstring pointer on
   `Task.complete`/`_code_fingerprint` (the ground truth a deep agent trusts over
   any doc) AND crisp SKILL.md prose for the agent who does not dig. The engine
   docstrings now draw the line precisely: the code FINGERPRINT (explicit
   `code_version` or, under auto, the AST hash) gates completeness and is
   authoritative; the separate advisory source-hash is warn-only and never gates.
   An agent must not collapse those two into "the hash merely warns".

5. **Rendered as terse prose, not tables.** SKILL.md is always-loaded; every row
   costs context on every activation. The verbs (auto rerun / verify / lock+bump /
   accept_code / reset) live inline in the iterate loop and the invalidation rules.
   A table would duplicate that at extra token cost - prose is the token-efficient
   choice, consistent with the two-tier-content principle.

All of it is gated `oryxflow >= 26.7.12` with a pre-26.7.12 reset fallback stated
where it applies; the supported floor stays 26.6.6 (the guidance degrades, it does
not require the new library). A live project's agent once assumed a current library
meant it was protected - under wave one that was false (the net was inert until a
task declared `code_version`). Wave two makes it TRUE by default, which is the
whole point of auto: correctness must not depend on memory OR on per-class
ceremony. So `/oryxflow:update-project` dropped the adoption pass entirely (there
is nothing to adopt); the only invalidation-related thing it does is report the
reset-before-run -> auto convention flip when its normal `CLAUDE.md` floor reconcile
produces it. An earlier draft had it flag a project that DISABLED auto, but that
inverted the point (auto is on by default; a project only has it off deliberately),
so it was cut.

The scaffold matches the default from day one, from the OTHER direction than wave
one did: the template `tasks.py` ships NO `code_version` (auto tracks the
placeholders' source; shipping one would LOCK them - the opposite of intent), and
the "Add a new task" recipe says to add the attribute only to lock an expensive or
hash-blind task. Consequence for releases: the template `CLAUDE.md` convention flip
(reset-before-run -> auto) is a scaffold-FLOOR change - update-project reconciles
`CLAUDE.md` - so it is floor-baseline-bump worthy (`26.6.29` -> `26.7.12`), unlike
the `tasks.py` placeholder edit (PROJECT bucket, never reconciled), which just
rides the release like any template change. The design requires LESS ceremony than
even wave one asked: the residual human cost is a per-task lock only where auto's
default is genuinely wrong, plus the verify habit - stated so agents neither treat
`code_version` as mandatory boilerplate nor trust an edit reran without checking.

## Scaffolding: the init command and the template

A new project is created by the `/oryxflow:init-project` slash command (commands
get a reliable `${CLAUDE_PLUGIN_ROOT}`; skills do not, so init is a command, not
the skill). It copies the bundled template into the user's cwd with a SHELL copy
(robocopy / cp -n), skip-existing / never-overwrite, and never reads+rewrites
files via the LLM (which would be slow and could corrupt `viz-template.ipynb`).

Git LFS setup is a SEPARATE command, `/oryxflow:init-gitlfs`, not folded into
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

## oryxflow is decoupled from luigi (do not assume otherwise)

oryxflow is NOT based on luigi. It once was a luigi wrapper (tasks subclassed
luigi's; `get_task_family` lived in luigi), but is now decoupled: base class is
`oryxflow.core.Task` (MRO `TaskPqPandas -> TaskData -> oryxflow.core.Task ->
object`, no luigi), and `get_task_family` returns `cls.__name__` in oryxflow's own
code.

Recorded because the "luigi wrapper" belief is a live trap: a stale-but-plausible
prior (true of old oryxflow, repeated in older docs / training data) that gets
recalled as fact, steering verification to read `luigi.*` to explain oryxflow -
and a leftover `import luigi` succeeding (transitive install) seems to confirm
it. The MRO check that catches it is the one most likely skipped.

Rule when reasoning about oryxflow internals (identity, caching, DAG): inspect the
installed class (`cls.__mro__`, then the method on the class that defines it),
never `luigi.*`; `import luigi` working is not evidence. Treat any "luigi" in an
older plan/doc as this slip. (The cache-safe-move guarantee under "Scaling a
growing project" is oryxflow's own, verified directly - only the luigi attribution
was wrong, not the fact.) More generally: distrust a library-internals claim
sourced from memory, not from the installed code.

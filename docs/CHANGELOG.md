# Changelog

> Compatibility: this plugin's skill guidance assumes `oryxflow >= 26.6.6` (the
> supported library floor - bump this line when the skill starts depending on new
> library behavior). The library `CHANGELOG.md` is the source of truth for
> API/behavior; when the two disagree about library behavior, the library wins.

All notable changes to the oryxflow plugin are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions are
date-based (`YY.M.D`, e.g. `26.5.30`). The top `## [Unreleased]` section is the
working bucket - it ships nothing until it is stamped with a version at release
time (see the Release section in the repo `CLAUDE.md`).

**Entry conventions** (make entries machine-consumable, so an agent can grep the
log to diagnose a regression). Three load-bearing tokens, matching the library's:

- A bullet-leading `BREAKING:` token when a change makes an *already-scaffolded*
  project out of date - it is the grep target. The plugin has no API, so its
  breaking surface is the scaffold floor, the commands, and the enforced
  conventions; a skill / docs / reference-only change is NOT breaking.
- A same-bullet `Migration:` clause naming the fix the plugin already ships:
  `/oryxflow:update-project` (scaffold-floor drift) or `/oryxflow:check-standards`
  (convention drift).
- Backticked symbols / command names / file paths (`` `/oryxflow:init-project` ``,
  `` `run.py` ``, a scaffold path) - never prose like "reworked the scaffold".

## [Unreleased]

<!-- Add bullets here as you work (Added / Changed / Removed). They stay
     UNPUBLISHED - plugin.json keeps the last released version, so consumers see
     nothing - until you cut a release: rename this heading to the new
     version + date, bump plugin.json to match, and add a fresh empty
     [Unreleased] back on top. See CLAUDE.md "Release". -->

## [26.7.12] - 2026-07-12

### Added
- Expensive-recompute guard guidance (`SKILL.md` + `reference.md`): an auto task
  whose last run exceeded `settings.code_version_auto_expensive_s` (default 600s)
  stays cached on a code change and warns with the exits (reset / `accept_code` /
  lock) instead of silently recomputing; the lock rationale (a) narrows to "manage
  by deliberate bumps even below the guard threshold". The scaffold `cfg.py` now
  ships the auto knobs as commented lines (`code_version_auto`,
  `code_version_auto_expensive_s`) so opting out is a visible, conscious choice.
- Lock-toggle semantics (`SKILL.md` + `reference.md`): the `code_version` line
  itself is stripped by the library's AST normalization, so typing it in /
  deleting / bumping it is a token change, never a source edit - adding or
  removing a lock on unchanged code never recomputes and never ripples
  downstream (records store both the token and the source hashes); an edit
  masked while locked-unbumped reruns when the lock comes off. `accept_code`
  never triggers downstream recomputes (the bare class form's caveat is "misses
  other tasks the same helper edit touched").
- `accept_code` visibility + upgrade path (`SKILL.md` + `reference.md`): it
  prints what it re-stamped ("nothing accepted" = wrong form - use the
  instance/`flow` form); the instance/`flow` form also stamps baseline records
  for outputs with no record yet, which is the answer to the `output predates
  current code` warning after an upgrade or fresh checkout (accept if current,
  reset if not). Staleness warnings dedupe per process on the printed channels;
  `result.warnings` and the event stream keep every occurrence.
- Code-aware invalidation guidance for `oryxflow >= 26.7.12` (`SKILL.md` +
  `reference.md`), reframed around AUTO invalidation (on by default,
  `settings.code_version_auto = True`): editing a task's `run()` or a helper it
  imports reruns that task and everything downstream automatically
  (comment/docstring/formatting edits never count), so the new iterate loop is
  edit -> run -> VERIFY it reran (the edited band shows in `result.ran` with
  reason `code change (auto: <files>)`); a `ran=0` after an edit means an auto
  blind spot (data file, installed package, dynamic dispatch, notebook-defined
  task) -> `reset` or lock the task. `reset` stays for what auto cannot see
  (changed source DATA at the loader task, corrupt cache, deleting outputs) and as
  the pre-26.7.12 fallback. `code_version` is now an opt-in LOCK (below), not the
  primary loop; `accept_code` (instance/`flow` form walks the upstream band) for
  an output-equivalent refactor; `keep_versions` for side-by-side versions of a
  locked task.
- Event-stream guidance (`SKILL.md` "Code-aware invalidation & the event
  stream"): session-start `oryxflow.events.print_status()` (prints the summary;
  `events.status()` returns the same facts as a dict and prints nothing),
  two-runs diff via
  `oryxflow.events.runs(task_family=, last=2)`, `self.logger` scalars persisting
  as `task_log` events, the `events.jsonl` / `events-YYYYMM.jsonl` head/offload
  file convention, and `MultiRunResult` aggregate accessors
  (`.ran`/`.reasons`/`.warnings`) instead of hand-rolled aggregation. The
  compatibility note in `SKILL.md` gates all of it on `oryxflow >= 26.7.12`;
  the supported floor stays `oryxflow >= 26.6.6`.
- Documented `code_version` as an opt-in LOCK, not a per-task ritual (`SKILL.md` +
  `reference.md` + `ml-patterns.md`): declaring it tells auto to STOP watching a
  task's source, so the task reruns only on an explicit BUMP and an unbumped edit
  merely warns. Lock a task for (a) an EXPENSIVE computation where an accidental
  refactor-driven recompute is costly - auto deletes and overwrites the old
  output, so pin a slow API pull or long backtest; (b) logic auto cannot see
  (dynamic dispatch, data-driven behavior). A locked task still reruns when an
  auto upstream changes (the fingerprint folds dependencies); a locked task's
  warning has the three risk-ranked exits (bump / reset / `accept_code`
  only-if-certain). Global escape hatch `settings.code_version_auto = False`
  reverts to pure opt-in for projects where auto is too fickle.
- Scaffold now relies on auto instead of arming a manual net: the template
  `tasks.py` placeholder tasks carry NO `code_version` (auto tracks their source
  from the first run; shipping one would LOCK them), and the "Add a new task"
  recipe (`SKILL.md`) says to add `code_version` only to lock an expensive or
  hash-blind task. `/oryxflow:update-project` dropped the old inert-net adoption
  pass entirely (auto needs no adoption); it just reports the reset-before-run ->
  auto convention flip when the normal `CLAUDE.md` floor reconcile produces it.
  All gated `oryxflow >= 26.7.12`; pre-26.7.12 scaffolds
  have no auto and keep reset-before-run. (The template `CLAUDE.md` convention
  change is the `BREAKING:` bullet under Changed below.)
- `/oryxflow:migrate` (`commands/migrate.md`) - restructures a messy data-science
  project (monolithic notebooks / linear scripts, hardcoded paths, magic
  constants, no caching) into a scalable oryxflow pipeline: maps the implicit
  linear flow to output-named, parameterized, cached tasks wired with
  `@oryxflow.requires`, then builds them up one task at a time. Map-then-build,
  `disable-model-invocation: true` (writes code), never deletes the source (it is
  the spec and the results oracle), offers to commit the result on verify (current
  or a new branch, the user's choice), and defers to `/oryxflow:init-project` when
  there is no scaffold to build into. Discoverable via `SKILL.md` step 0 when a
  directory holds ad-hoc DS work but no oryxflow wiring. (This is the reserved
  `migrate` feature - distinct from the `d6tflow` -> `oryxflow` rename doc.)
- `skills/oryxflow/d6tflow-migration.md` - an on-demand playbook for migrating a
  `d6tflow`-era project to `oryxflow` (a whole-word `d6tflow` -> `oryxflow` rename
  across `*.py`, deps files, the data doc, and any `*.ipynb`/`*.html`, applied as
  ONE word-boundary substitution scoped to the grep-matched files - not per-file
  hand `Edit` calls; plan-then-apply; checks the installed `oryxflow` version
  against the compat floor and leaves the `pip install`/upgrade as an explicit
  user decision). Carves the one exception to the no-hand-written-nbformat-JSON
  rule (a token swap can't corrupt cell JSON the way authoring can), and offers to
  commit the rename on completion (current or a new branch, the user's choice).
  Invoked by
  the user naming it - NOT a slash command and NOT auto-triggering; discoverable
  via a pointer in `SKILL.md` "Additional Resources". (Distinct from the
  `/oryxflow:migrate` command above, which restructures a messy project.)
- A `Compatibility:` contract stating the supported library floor
  (`oryxflow >= 26.6.6`) in two homes - `SKILL.md` (so the installed agent has it
  without a fetch) and authoritatively at the top of `docs/CHANGELOG.md`. The
  skill compares it against `oryxflow.__version__` and REPORTS skew instead of
  debugging a phantom when the running library is older than the skill assumes;
  authority is split (library `CHANGELOG.md` wins on API/behavior). The floor moves
  only when the skill starts depending on new library behavior, not per release.
- A "Diagnosing a regression / version bump" pointer block in `reference.md`
  (triggered from `SKILL.md` "Additional Resources"): on an unexpected
  `AttributeError` / `ImportError` / `TypeError` or right after a version bump,
  confirm `oryxflow.__version__`, then grep the changelog for the failing symbol
  from the installed version forward, `BREAKING:` first. Links the library and
  plugin changelogs via `raw.githubusercontent.com` (clean markdown to fetch). No
  changelog content is inlined into the skill - just the pointer.
- Changelog entry conventions header in `docs/CHANGELOG.md` documenting the three
  load-bearing tokens (`BREAKING:` grep target, same-bullet `Migration:` clause,
  backticked symbols/commands/paths), mirroring the library's changelog so an agent
  can grep the log to diagnose a regression.
- `README.md` "Best practices" and "What's new" sections that LINK (do not
  duplicate) `conventions.md`, `ml-patterns.md`, and `docs/CHANGELOG.md`, and state
  the pull-based update reality (`/plugin marketplace update oryxflow`).
- `.githooks/pre-commit` now also guards that the compatibility floor AGREES across
  `SKILL.md` and `docs/CHANGELOG.md`, and lints that every leading `BREAKING:`
  changelog bullet carries a `Migration:` clause.

### Changed
- BREAKING: the template `CLAUDE.md` scaffold-floor convention flipped from
  reset-before-run to AUTO for code changes - it now says an edited task reruns
  automatically (just verify it did), with `code_version` as an opt-in lock for
  expensive/hash-blind tasks and `reset` narrowed to changed source DATA (at the
  loader task), a corrupt cache, or deleting outputs. A project scaffolded before
  this still carries the old reset-centric convention. Migration: run
  `/oryxflow:update-project` to reconcile its `CLAUDE.md`. Floor baseline bumped
  `26.6.29` -> `26.7.12` so the skill nudges older projects to it.
- Swept `docs/CHANGELOG.md`: the `26.6.29` scaffold floor-stamp entry is now a
  `BREAKING:` bullet with a `Migration:` clause (`/oryxflow:update-project`), since
  a project scaffolded before it lacks the stamp and never sees the staleness
  nudge. Other existing entries are additive and left as-is.

## [26.7.11] - 2026-07-11

### Changed
- `conventions.md` now addresses the coding agent directly (second person)
  throughout its framing, instead of a human reader or the agent in the third
  person ("the AI agent working in it", "the agent should be PROACTIVE", "How We
  Organize", "our convention"). The rules and the pedagogical rationale are
  unchanged - only the voice, so the on-demand file reads as instructions FOR the
  agent, not a description ABOUT it. Added an "address the agent directly"
  authoring convention to `CLAUDE.md` to keep skill files agent-facing.
- README Install section now states updates are pull-based: there is no push
  channel, so run `/plugin marketplace update oryxflow` periodically to pick up
  new releases (the CHANGELOG lists what changed).

## [26.7.3] - 2026-07-01

### Changed
- Report-notebook naming now says the `<topic>` must be subject-first with enough
  context to read standalone, because the rendered `viz-<topic>.html` is consumed
  detached from the project (emailed, dropped in a channel): `viz-benchmark-coverage`,
  not a bare `viz-coverage` - infer the subject from the tasks the report loads or
  the project's purpose. Sharpened in place (no new rule) in SKILL.md "Render /
  publish a notebook", `conventions.md`, and the scaffold floor `CLAUDE.md`.
- Scaffold `run.py` now captures the `RunResult` and prints `result.summary()`
  instead of discarding a bare `flow.run()`, and comments the drill-down
  (`result.ran`/`.complete`/`.did_run`, and `.failed`/`.failure_of` via
  `abort=False`). The structured "what ran / what failed" is now in captured
  stdout, so there is no reason to scrape a finished run's log for status. The
  skill's "See what ACTUALLY ran" block, `reference.md` run/WorkflowMulti
  examples, and the scaffold floor `CLAUDE.md` gained the matching one-line
  guidance; `WorkflowMulti.run()` returns a `MultiRunResult` that carries the
  same `.summary()`/`.success`, so the habit is uniform across single and multi
  flows.

## [26.7.2] - 2026-07-01

### Added
- New command `/oryxflow:check-standards` - a check-and-recommend pass over project
  code against the house standards for readable, reliable code: NAMING (tasks,
  columns, variables, `eda/utils/viz` modules), CODE STYLE (ASCII-only,
  `self.logger`, no try/except, off-the-shelf libraries, no inline Python), and
  DOCSTRING contracts. Loads the skill + `conventions.md` as the rubric, defaults
  to the working-tree diff, reports findings with a concrete fix each, and edits
  only what the user approves. A companion `/oryxflow:cleanup-tasks` (consolidate
  repeated calls / reused data into cached tasks) is reserved.

## [26.7.1] - 2026-07-01

### Added
- SKILL.md "Render / publish a notebook" now leads with how to READ a notebook:
  use `Read` (renders `.ipynb` cells + outputs natively), or read the already-
  rendered HTML in `reports/render/` when present - and do NOT dump raw cell JSON
  or pipe through `nbconvert --to markdown` to read it (truncates cells, drops
  outputs; that command is only for extracting chart images). The section
  previously covered only PRODUCING notebooks, so the agent defaulted to inline
  `json.load` / nbconvert to read one.
- Scaffold now ships `reports/render/images/` (gitignored via the existing
  `reports/render/` rule). The skill's "visually check a chart from a notebook"
  step (SKILL.md) now points `jupyter nbconvert --to markdown --output-dir` at
  this dir instead of an unspecified `<dir>`, and warns against a system temp
  path. Fixes a real run where the agent sent nbconvert output to a temp dir
  that did not exist and got a PermissionError.

### Changed
- SKILL.md "Run from the working directory" broadened to "never `cd`": the rule
  was framed around python project commands, so the agent still `cd`'d for other
  tools (`jupyter nbconvert`, `cp`). It now says EVERY command runs from the root
  as-is, names those tools explicitly, and notes that a `cd` + output redirection
  forces a manual approval prompt.
- Column-naming guidance both deepened in `conventions.md` and reinforced at the
  point of decision (the rule was correct but lived only in on-demand
  `conventions.md`, so an agent naming columns off the floor on pandas-agg
  autopilot never met it). `conventions.md` "Column naming" gained: (a) name a
  derived metric for WHAT IT MEASURES - the domain word must be in the name
  (`win_rate`, `benchmark_coverage_pct`), never a bare unit/stat PREFIX
  (`pct_x`, `avg_x`) that hides the metric; (b) an extended derive-by-suffix
  vocabulary - unit tags (`_usd`/`_local`/`_eur`) and series aggregations
  (`_avg`/`_min`/`_max`/`_median`/`_std`), stacked innermost->outermost =
  transform, unit, aggregation, so a stat is the OUTERMOST suffix and siblings
  sort adjacently (`benchmark_coverage_pct_avg` / `_min` / `_max`); and (c) a
  Don't/Do table plus a worked count/ratio family (the `X_total` / `X_covered` /
  `X_coverage_pct` triple sharing ONE leading subject token - shape
  `{subject}_{concept}_{unit}`, e.g. `user_churn_rate` because the counts are
  `users_total` / `users_churned`; purpose-first is allowed only when applied to
  all three) with the trap-resolving contrast - a leading STAT/unit (`avg_`, `pct_`, `n_`) is wrong
  and must be a suffix, but a leading SUBJECT family word (`yield_`, `price_`,
  `return_`) is correct. The rule is now also placed where
  the agent acts: the scaffold `CLAUDE.md` non-negotiables carry a compact naming
  bullet - the one shared rule for columns / tasks / variables (subject-first
  broad->narrow), the column suffix rule with concrete rewrites, the
  purpose-named metric + shared-stem family (`X_total` / `X_covered` /
  `X_coverage_pct`), and the task noun-for-output rule; the "add / rename an
  output column"
  recipe (SKILL.md) says to name suffix-style and check the table when writing
  `.agg()` / `.rename()` / a column list; and the scaffold `docs/oryxflow-data.md`
  points to the conventions (its job is to record THIS project's canonical names,
  not restate house rules). Fixes a real project where the agent produced
  stat-prefixed names like `avg_x` / `pct_x` on pandas-agg autopilot. (No
  linter/hook: a prefix regex would flag the plugin's own blessed
  `return_`/`price_` families.)
- Multi-parameter execution is now documented as an idiom. reference.md's
  `WorkflowMulti` example (Pattern 1) switched from the list form (integer keys)
  to the idiomatic named-dict form (`{'lgbm': {...}, 'xgboost': {...}}`), showing
  `flow=name` selection, the all-flows `{name: output}` return, per-flow reset,
  the list/cross-product variants, and `runLoad` as the single-param one-call
  helper. SKILL.md's Workflow concept gained a one-line pointer: compare a fixed
  named set of params via one `WorkflowMulti` keyed by name (still one importable
  object). Fixes a real project where the agent had to inspect the package to
  confirm the API the skill under-documented.
- SKILL.md's Additional Resources footer is now an escalation rule, not a passive
  link list: when the skill lacks an API, confirm against the INSTALLED package
  first (`inspect.signature`, `cls.__mro__`) as version-matched ground truth, then
  the online docs - and on conflict the installed code wins (the online docs can
  lag the luigi decoupling).
- Skill orientation (SKILL.md) now handles an EMPTY / not-yet-oryxflow directory
  as an explicit first case: when no `tasks.py` / `flow.py` is present, the skill
  stops hunting for pipeline files and CONFIDENTLY recommends
  `/oryxflow:init-project`, leading with the payoff (a runnable, reproducible
  pipeline - parameterized tasks, intelligent caching, a clean
  tasks/flow/run/cfg layout instead of ad-hoc scripts) and ending with a clear
  call to action for the user to type `/oryxflow:init-project`, rather than
  presenting a tentative menu of options. The recommendation is explicit that the
  skill CANNOT invoke the command itself (it is manual / `disable-model-
  invocation`, and the skill lacks the plugin root to scaffold inline) - so it no
  longer says "want me to run it?", which wrongly implied Claude could. Previously
  the orientation steps assumed the scaffold files existed, so an empty dir was
  handled ad hoc.
- `/oryxflow:init-project` copy step (init-project.md) now names `robocopy` as the
  explicit DEFAULT on Windows (use it consistently; do not improvise `cp` /
  `Copy-Item` instead) and documents that robocopy exit codes 0-7 are SUCCESS
  (1 = files copied), so exit code 1 must not be treated as an error or retried -
  only >= 8 is a real failure. Fixes runs that flip between robocopy and cp, or
  abort a successful scaffold on the benign exit-1.
- "Run from the working directory" rule (SKILL.md) now covers EVERY project
  command, not just `run.py` / `visualize.py`: `python -m eda.<subject>.<name>`
  probes are explicitly included, and the rule spells out that the session shell
  already starts in the project root, so prepending `cd "<path>" && ...` is
  redundant and breaks on spaced paths. Stops the recurring habit of `cd`-ing into
  the project before every `python -m` probe.

## [26.6.29] - 2026-06-29

### Added
- New command `/oryxflow:update-project` - the maintenance counterpart to
  `/oryxflow:init-project`; reconciles an existing project's scaffold floor
  against the latest bundled template. It loads the `oryxflow` skill, sorts every
  template file into FLOOR (reconcile by default: `CLAUDE.md`,
  `viz-template.ipynb`), LOW-CHURN (additive / on demand only: `.gitignore` -
  which `/oryxflow:init-gitlfs` owns - and `.creds.yaml.example`), SKELETON
  (structure only: `docs/oryxflow-data.md`), or PROJECT (never touch: `tasks.py`,
  `flow_params.py`, `cfg.py`, `flow.py`, `run.py`, `visualize.py`), then proposes
  a per-file migration plan and applies it only after the user confirms. Closes the gap
  where older projects miss newer floor conventions (e.g. the
  skill-availability check) and `/oryxflow:init-project` deliberately will not
  overwrite an existing `CLAUDE.md`.
- Code Style rule (SKILL.md) "Use off-the-shelf libraries; do not reinvent the
  wheel": reach for the established library (statsmodels / scipy / sklearn for a
  regression, statistical test, or time-series model) instead of hand-rolling the
  math, and treat a failed import as a broken ENV - STOP and offer to fix it
  rather than routing around the error by reimplementing the library. ml-patterns.md
  "Best practices" carries the ML elaboration (probe submodules on an ABI clash;
  the one legitimate reason to wrap a library is a documented data quirk, and even
  then build on the library and validate against it).

### Changed
- BREAKING: the scaffold floor `CLAUDE.md` now carries a floor-version stamp
  (`<!-- oryxflow-floor: VERSION -->`), set to the plugin version of the last
  floor change. The `oryxflow` skill reads it on orientation and nudges (once, no
  nagging) toward `/oryxflow:update-project` when the stamp is missing or older
  than the current floor baseline - so older projects discover the command
  without the user having to know it exists. The baseline tracks *floor* changes,
  not every release, so floor-unrelated version bumps do not trigger false
  "stale" nudges. `/oryxflow:update-project` rewrites the stamp when it migrates.
  A project scaffolded before this release has no stamp and never sees the
  staleness nudge. Migration: run `/oryxflow:update-project` to add the stamp and
  reconcile the floor `CLAUDE.md`.

## [26.6.28] - 2026-06-28

### Changed
- Standardized multiple-output tasks on `persists` (plural) across `reference.md`
  and `ml-patterns.md`; `persist` (singular) is documented as a
  backwards-compatible alias for the same attribute. Fixed the misleading
  ml-patterns comment that implied `persist` vs `persists` switched
  list-vs-dict output - that is decided by what you pass to `save()`
  (`[...]`+`from_list=True` vs `{...}`), not the attribute name.
- Fixed a dangerous input-loading example in `reference.md`: the old
  `self.input()[0].load(persist='train')` is wrong twice over - `[0]` indexes
  the dependency (not a persist output), and `persist=` is not a valid selector.
  Since `load()`/`inputLoad()` take `**kwargs`, the bad selector was SILENTLY
  ignored and returned the whole output. Rewrote the "Loading Data from Upstream
  Tasks" section with the correct selection rules (`self.input()` mirrors
  `requires()`; outputs select by name via `keys=`, deps via `task=`/index;
  prefer the named-dict `requires({...})` form) and a warning about the silent
  unknown-kwarg trap. Added a one-line `inputLoad()` (returns data) vs `input()`
  (returns the raw target) rule, and made `ml-patterns.md` consistent (its lone
  `self.input().load()` -> `self.inputLoad()`).
- Scaffold floor `CLAUDE.md` "oryxflow plugin" section now tells Claude to check
  the `oryxflow` skill is available before real workflow work (editing the flow
  files or running the pipeline), and if not, to say so and ask the user to load
  it - then, without nagging, to occasionally remind the user after substantial
  work that they get better results with the plugin active. Replaces the soft
  "if installed" note; catches a silently unloaded plugin (Claude editing without
  the skill's depth) at the moments it matters, while keeping the file a portable
  floor that still works without the plugin.
- SKILL.md "run as a module" rule now covers ANY project script in a subfolder
  that imports the flow (EDA probes, but also `reports/` / `utils/` scripts), not
  just `eda/` - and notes that `python -m pkg.name` puts the root on the path, so
  the `PYTHONPATH` workaround (PowerShell `$env:PYTHONPATH=...`) and `sys.path`
  patching are unnecessary. Root-level scripts (`run.py`, `visualize.py`) still run
  directly. Mirrored the PYTHONPATH point into the scaffold's project `CLAUDE.md`.

### Added
- `reference.md` parameter-types list now includes `ChoiceParameter(choices=[...])`
  and `EnumParameter(enum=...)`. `ChoiceParameter` is the recommended fail-fast
  option for string categoricals (e.g. `model='rf'`): an off-list value raises at
  task construction, not deep in downstream code, with zero churn to existing
  string values. `EnumParameter` gives the same guarantee but requires defining an
  `enum.Enum` and rewriting values - noted as the heavier choice.
- SKILL.md now documents the `RunResult` returned by `flow.run()` as the agent-
  facing way to confirm what ran: `result.did_run(tasks.X)` (confirms a reset
  took), `result.ran`/`.complete`/`.failed`, and `flow.run(abort=False)` +
  `result.failed[0].traceback` to diagnose a failure WITHOUT re-running (default
  `abort=True` raises before returning). Corrected the Execution Summary example
  (dropped a stray `- 1` item prefix; the logged luigi-compatible block still
  prints via `RunResult.__str__` when `enable_logging` is on).
- `reference.md` "Load / save cheat-sheet" table: pick the identifier by WHAT
  (data vs meta) x WHERE (inside `run()` vs outside with a `flow`) x HOW MANY
  (all vs one) - e.g. load one output `self.inputLoad(keys='a')` inside vs
  `flow.outputLoad(Task, keys='a')` outside; meta `self.metaLoad(key=0)` vs
  `flow.outputLoadMeta(Task)`. Folds in the by-name-not-by-index rule and the
  silent-unknown-kwarg trap as table notes.
- Logging convention (two layers), replacing the old `print("SUCCESS:/WARNING:/
  ERROR:")` prefixes: `oryxflow.enable_logging()` for task lifecycle, `self.logger`
  inside `run()` for DOMAIN signal (shapes, drop rates, metrics, the branch taken).
  Rule: log scalars + lifecycle, SAVE rows + artifacts (`self.save()` / xlsx),
  never per-row. Examples use `self.logger`, NOT a raw `from loguru import logger`:
  `enable_logging()` filters to the `oryxflow` namespace and drops loguru's default
  handler, so a raw task-module `logger.info` is silently dropped - only
  `self.logger` (the `Task.logger` property) survives (and auto-tags `task_id`).
  Color is one switch, `enable_logging(colorize=False)` (auto-detects TTY vs
  redirected), since domain logs now share the one oryxflow sink - the old
  `logger.add("run.log", colorize=False)` side-sink is gone. In SKILL.md Code
  Style + scaffold floor `CLAUDE.md`; ML depth + the `training cutoff` model
  example in `ml-patterns.md` ("Logging in ML tasks") + log lines in the
  `FeaturesTransform` / `ModelTrain` templates. Scaffold `run.py` / `tasks.py`
  model it (`run.py` uses `print` for its banner - no `self` outside a task).
- SKILL.md "Reading the run output" consolidates how to read a run: read it
  straight (don't tee-and-grep), Execution Summary first (what recomputed vs
  cache-hit), numbers from saved artifacts not scraped logs, read clean via
  `enable_logging(colorize=False)` or anchor greps on a token, and "no metric
  line" usually means wrong logger (raw loguru) not no signal.
- Reset / cache-invalidation rule promoted to the always-loaded tiers: oryxflow
  caches on identity (class + params), NOT code, so a CODE/DATA change needs
  `flow.reset(Task)` (cascades downstream) - and since it cascades, NEVER write a
  reset helper. A PARAMETER change auto-reruns; if not, fix the parameter
  definition / inheritance. Now in the scaffold floor `CLAUDE.md` + SKILL.md
  "Modify an existing task"; depth + force-run alternatives in `reference.md`.
- `ml-patterns.md` Productionizing: softened `env=prod/dev` - `env` is a
  project-chosen label (also e.g. `utest` for a shareable sampled subset), not a
  universal scheme.
- SKILL.md "Read output straight from the run" rule: run scripts in the
  foreground and read captured stdout directly - simpler than teeing output to a
  temp-dir log (`Tee-Object $env:TEMP\...`, `Select-Object -Last N`) and re-reading,
  or backgrounding-then-polling with `sleep`+`tail`. For a long run, background it
  and wait for the completion notification, then read once. Verbosity is best
  controlled at the source (`loguru` levels / an optional file sink), not by
  filtering the stream after the fact.
- "Scaling up: organizing a growing project" section in `conventions.md`,
  replacing the old thin (and internally inconsistent) "Alternative Structures"
  block. Codifies a graduated progression for a growing `tasks.py` - (a) one
  chain-ordered file, (b) naming families, (c) comment section-header blocks
  (the cheap organizer that carries a file well past ~500 lines), (d) split into
  `tasks_<phase>.py` modules only when GENUINELY long (~1000 lines / ~20+ tasks)
  or a separable subsystem appears, cutting along the section seams. Two split
  axes: phase (imports upstream-only -> acyclic) and subsystem (the group-by-
  subject rule applied to tasks; subdir package when it bundles its own helpers).
  After splitting, a slim `tasks.py` SPINE holds the project-goal docstring +
  orchestration tasks and imports the phase modules - NOT a re-export aggregator
  (direct imports avoid cycles). One `flow_params.py` carries both experiment
  `params` and a frozen `params_prod`. App/reporting subsystems go at the project
  root with their own `cfg_app.py` + launcher, importing the flow and
  `outputLoad`ing (never reading `data/`). Splitting is cache-safe: a task's
  identity is its class name (`task_family`), not its module path - VERIFIED
  empirically (same class in two modules -> identical `data/<Class>/` path); only
  RENAME orphans a cache, MOVE is free.
- "Productionizing: prod vs experiment" section in `ml-patterns.md`: the
  going-to-prod lifecycle. `params_prod` defined once and IMPORTED by the prod
  orchestration (not re-hardcoded - fixes a real duplication); a `RunAll...Prod`
  task that loops prod variants with SELECTIVE resets (refresh data layers, keep
  `ModelTrain` frozen/cached); `env=prod/dev` data segregation; a periodic-
  refresh protocol. Plus a "Productionize a research project / notebook"
  subsection: sort messy notebook cells into the standard phase-task bins (load
  -> features -> model -> eval -> predict), wire the DAG, then add prod
  orchestration - the no-inline-Python rule applied to a whole notebook.
- Proactive "Graduating a growing project" nudge rule in `SKILL.md`: on a real
  trigger MID-EDIT (going to prod / a separable subsystem appears / a genuinely
  long `tasks.py`), OFFER the next structural step - but NOT on raw task count
  (one sectioned file scales far) and NOT on a plain orientation load (stays
  lightweight). Data scientists tend to under-organize, so the agent leads here.
- Example invocations in `SKILL.md`'s Build group: "split `tasks.py` along its
  sections into modules", "set up a prod run with frozen params".

### Changed
- Fixed the older inline `tasks.py` hint in `conventions.md` ("can split into
  `tasks_etl.py` / `tasks_models.py`") to point at the new "Scaling up" section
  instead of giving a second, divergent splitting rule.
- Upgraded `ml-patterns.md`'s "Task organization checklist" item 7 (`RunAll`) to
  mention the `RunAll...Prod` twin and point at the new productionizing section.
- `SKILL.md` code-organization block now points to "Scaling up" for when/how a
  project graduates. Architecture playbook + component table updated:
  conventions.md owns scaling LAYOUT, ml-patterns.md owns the PROD lifecycle.
- Template `CLAUDE.md` notes the project can scale (section-headers -> split) with
  a pointer to the plugin's "Scaling up" guidance.
- README install instructions point at the public GitHub repo
  (`d6t/oryxflow-claude-plugin`) instead of `<owner>/<repo>` placeholders, and the
  Resources section now links the public repo. Added a `repository` field to
  `plugin.json`. The full HTTPS URL is now the primary install command (works
  for everyone with no auth), with the `owner/repo` shorthand as a secondary
  option noted to fail on some SSH setups.

## [26.6.22] - 2026-06-22

### Added
- "Avoiding silent data errors" section in `reference.md` (pointer in `SKILL.md`):
  the trap class that yields a WRONG NUMBER WITHOUT RAISING, which is the most
  dangerous for an AI agent. Four guards - validate every merge (`validate='m:1'`
  + row-count check, the usual cause of silent row blow-up), look at the frame
  (shape/dtypes/NA/`describe` + reconcile aggregates) before stating a finding,
  quote numbers pulled from the frame (never eyeballed off a chart), and watch
  pandas index alignment in arithmetic. Distinct discipline from "assert your
  inputs" (make the failure LOUD), so it is named separately.
- One-line lead-in over the naming rules stating the throughline behind all of
  them: a name is something the reader holds and can mis-apply, so every
  convention pushes one way - fewer translation layers, self-describing tokens,
  shared family prefixes - and unspecified naming cases are decided by that
  principle.
- Column-naming convention (optimizes for assistant accuracy by minimizing name
  layers): carry ONE canonical `descriptive_snake_case` name per column, renamed
  from raw codes ONCE at ingestion and never re-aliased downstream (no
  code->display->code round-trips); order tokens broad->narrow (category first,
  opposite of English) so families share a leading prefix and cluster
  (`rate_construction`, `rate_completion`; not `construction_rate`); derive by a
  small fixed suffix vocabulary with the operation LAST (`_yoy`, `_yoy_pp`/`_diff`,
  `_pct`, `_ma{n}`, `_lag{n}`, ...) so the name carries provenance + transform;
  apply Human-readable Title Case labels ONLY at the `viz/` plotting layer; record
  the raw->canonical map in `docs/oryxflow-data.md`. Full section in `conventions.md`
  ("Naming"), pointer in `SKILL.md`. Motivated by a real three-layer
  round-trip (raw `uc_rate` -> display `Under Construction Rate` -> analysis
  `uc_rate` again) that caused wrong-column confusion. The broad->narrow ordering
  also extends to TASK names (a family shares a leading token - `FundamentalsAll`,
  `FundamentalsSignals`, `FundamentalsLeadLag`, not `LeadLagAnalysis`; added to the
  task "Naming" sections) and to DataFrame / variable names (`df_profile_division`
  / `df_profile_cbsa` cluster; keep `df_X`/`df_y`/`df_train`/`df_test`).
- New `/oryxflow:init-gitlfs` command (`commands/init-gitlfs.md`) - puts a
  project's `data/` under Git LFS. It checks the git-lfs binary is installed AND
  that `git lfs install` has hooked LFS's filters into git (guiding the user to
  `winget install GitHub.GitLFS` / `brew install git-lfs` if missing), ensures a
  git repo on `main` (`git init -b main` if needed), comments the data-files
  block in `.gitignore` to un-ignore data, runs `git lfs track "data/**"` and
  `git lfs track "reports/render/**"`, and commits `.gitattributes` + `.gitignore`.
  Un-ignoring happens BEFORE tracking so data does not bypass LFS; committing the
  actual data is left to the user.
  Manual (`disable-model-invocation: true`), like init-project.
- The project scaffold now ships an `eda/` package root (`eda/__init__.py`) so a
  new project can run probes as `python -m eda.<subject>.<name>` without first
  creating the package by hand.

### Changed
- Split the on-demand depth in two along the library-vs-conventions seam.
  `reference.md` had crossed ~1000 lines, so a focused question ("where does this
  code go", "how do I name this") had to page the whole file. New
  `conventions.md` (house style: project-layout deep dive, code-organization-by-
  subject, and naming columns/tasks/variables) is now a sibling on-demand file;
  `reference.md` keeps the oryxflow LIBRARY (task types, params, running/reset,
  patterns, recipes, debugging, silent-data-error guards). Moved the three
  sections out of `reference.md`, left a pointer, and updated routing in
  `SKILL.md` (header + inline pointers), `architecture.md` (component table, load
  tiers, playbook), and `design-notes.md` (rationale for the split + the stopping
  rule: one seam, not many files).
- Documented how to VISUALLY check a chart (the agent confirming a figure it
  produced is readable), since `Read` truncates a notebook's embedded base64 image
  outputs. Keyed on where the plot is made: from `viz/<subject>.py` code, the
  plotting/runner function `savefig`s to a file and you `Read` it (throwaway ->
  `data/.eda/<subject>/`, deliverable -> `reports/render/`); from a notebook, do
  NOT add `savefig` to cells - `nbconvert --to markdown` extracts the output images
  to PNGs you `Read`. Never hand-decode base64 from the `.ipynb`. In `SKILL.md`.
- Report notebooks are now template-based. The scaffold ships the notebook as
  `viz-template.ipynb` (was `visualize.ipynb`); the convention is one-report-per-
  notebook - copy the template to a subject-named `viz-<topic>.ipynb` at the root
  and edit the copy, never the template in place (which a session had done,
  consuming it and tying one report to the generic name). `--output-dir` then
  renders `reports/render/viz-<topic>.html` for free. Renamed the template file and
  updated all references (`SKILL.md`, `reference.md`, template `CLAUDE.md`,
  `init-project.md`, root `CLAUDE.md`, architecture, design-notes). `visualize.py`
  is unchanged - it has a different lifecycle (graduates into `viz/<subject>.py`).
- Rebuilt `viz-template.ipynb`'s contents. Dropped the `tasks.GetData` placeholder
  (loads the FINAL task via `flow.outputLoad()` instead, so it works on any
  project), cleared the baked-in stale outputs, dropped the unused `seaborn`
  import, and added guidance + section headers. Now demonstrates the modern load
  patterns: `flow.outputLoad()` / `outputLoad(tasks.X)` and parameterized,
  multi-output `oryxflow.runLoad(tasks.X, params={...})` - including `reset=True`
  after a code edit and loading two variants to compare (the region-vs-metro case).
- Notebook authoring now points at the `NotebookEdit` tool instead of hand-writing
  nbformat JSON via `Write` (slow, easy to corrupt). `SKILL.md`'s "Render / publish
  a notebook" section says to edit cells with `NotebookEdit` (and `Read` to inspect
  cells + outputs); notes that it has no kernel, so outputs come from the nbconvert
  `--execute` step; and optionally offers a Jupyter MCP server for a live
  write-run-inspect-fix loop (the publish path does not need it).
- Sharpened the "load a task's data, don't re-read the source" rule against the
  cold-start (`/clear`) failure where the model shell-`head`s the raw input CSV
  even though the data already exists as a task's output. The rule is now: once a
  task produces the data, `flow.outputLoad(Task)` it - don't go back to the raw
  source to learn the (renamed/derived) output's schema. It is deliberately NOT an
  absolute ban on reading raw files: doing so is the normal way to bootstrap a
  loader task for source not yet in the pipeline. Wording put in BOTH `SKILL.md`
  and the always-loaded template `CLAUDE.md` - the latter governs before the
  activation-gated skill applies. Rationale in `design-notes.md` ("Three-layer
  model" corollary).
- Documented adding/removing/renaming an output column as a first-class operation.
  The reset/iterate mechanics already covered it generically, but it was unnamed,
  not in the activation triggers, and missing from the in-session example list
  (the most common iterate op wasn't offered). Now: `when_to_use` names it;
  `SKILL.md` adds it to the offered Build examples and gives the "Modify an
  existing task" loop a column-specific note (update the docstring `Out:` list;
  removing/renaming breaks downstream readers - fix them in the same edit);
  `reference.md` adds the depth case (a silent semantic change to an existing
  column does not error downstream); README's "Things you can ask" stays in sync.
- Sharpened the "trust auto file management" rule into an explicit do/don't: never
  hand-read a task's data off disk (`pd.read_excel(path)` / `pd.read_csv(path)`) -
  use `flow.outputLoad(Task)` or `self.inputLoad()`. The rule existed only as
  "don't stat the filesystem" (existence check) and the loader-task "don't re-read
  a csv"; this names the content-loading anti-pattern directly. Added to `SKILL.md`
  and the template `CLAUDE.md`.
- Task docstrings no longer carry "see `docs/oryxflow-data.md`" cross-references.
  The conventions already establish that doc as the data home, so a pointer in
  every docstring is noise (and ages badly as the data layer grows). `SKILL.md`
  now says to state quirks inline and explicitly NOT to tack on the cross-ref;
  the worked example drops its trailing pointer.
- Carved out a scratch exception to the "`eda/` is read-only" rule. A probe still
  produces no pipeline artifact in `data/`, but genuinely disposable scratch (an
  iterated cache, an intermediate to eyeball) may go to `data/.eda/<subject>/` -
  gitignored via the `.*` rule (which sits outside the data-files block that
  `init-gitlfs` un-comments, so scratch stays untracked even in an LFS project)
  and regenerable. New "Scratch for probes" subsection in `reference.md`, one-line
  pointer in `SKILL.md`.
- Recording a material finding is no longer gated behind a confirmation. `SKILL.md`
  and the template `CLAUDE.md` now separate two moments: deciding to GO exploring
  stays opt-in (the user's call), but writing up a finding a probe has ALREADY
  produced - especially a data-quality finding - is part of finishing the work and
  is done without asking. Closes the case where the skill ran a check, surfaced a
  quality issue, then asked "shall I record this?" instead of recording it.
  Rationale in `design-notes.md` ("EDA is a learning artifact").
- Dropped the "vendored mirror" policy for `resources/template-minimal/`. The
  scaffold is now edited directly in this repo (canonical here) instead of being
  re-synced from a separate `oryxflow-template-minimal` source repo. Updated
  `CLAUDE.md`, `architecture.md`, and `design-notes.md` accordingly.
- Broadened skill activation triggers in `SKILL.md` frontmatter: `description`
  and `when_to_use` now name loading / cleaning / transforming / analyzing data
  (each phrased as "becomes a task"), so plain-language data-prep requests like
  "clean the data" reliably auto-activate the skill from a cold context, not only
  task/flow-shaped phrasings. No behavior change once active.
- Renamed `/oryxflow:project-init` to `/oryxflow:init-project`
  (`commands/project-init.md` -> `commands/init-project.md`) so the two setup
  commands share an `init-*` prefix. Updated all references (README, CLAUDE.md,
  architecture, design-notes). The command's behavior is unchanged.

## [26.6.6] - 2026-06-06

### Changed
- Hardened the no-inline-Python rule in `SKILL.md` to close the "quick probe"
  loophole. The rule was obeyed for real EDA scripts but rationalized away for
  small one-off `python -c` sanity checks ("it is just a tiny test"). The wording
  now states explicitly that quick / one-off / throwaway probes are included - a
  one-line `python -c` still goes in an `eda/` file - and gives the why (an `eda/`
  file is near-free, is re-runnable next session, and `python -c` breaks on
  Windows shell quoting), so it reads as a reason rather than a prohibition the
  model can argue around.
- `SKILL.md` now requires EDA probes to be documented, not just relocated: each
  `eda/` script states the question it answers (docstring) and makes its result
  legible (print / recorded comment), and material findings (schema, quirks,
  quality issues, business rules) get promoted into `docs/oryxflow-data.md`. An
  `eda/` script is throwaway as code, but its finding is not - capturing it is
  what spares the next session from re-deriving it. Rationale recorded in
  `docs/design/design-notes.md` ("EDA is a learning artifact, not throwaway").
- New code-organization convention: group supporting code by SUBJECT (a task or a
  dataset, snake_case) into `eda/<subject>/<name>.py` (probes),
  `utils/<subject>.py` / `utils/__init__.py` (helpers), and `viz/<subject>.py` /
  `viz/__init__.py` (plots); a helper shared by 2+ subjects goes in a concept /
  dataset module (concept by default), one subject's helper in `utils/<subject>.py`,
  only truly generic helpers in `__init__.py`. The no-inline-Python EDA path is now
  nested - `eda/<subject>/<name>.py` run as `python -m eda.<subject>.<name>` (each
  folder an `__init__.py`), updating the old flat `python -m eda.<name>`. Decisions:
  snake_case modules; code that builds a `data/` input prefers a real source task;
  non-task reference data groups under its dataset; filenames name the specific
  check (no bare `verify.py`); extract on the 2nd use. Tight summary in `SKILL.md`,
  full rules + edge cases in `reference.md`, rationale in `design-notes.md`.
- Notebook policy: notebooks that import the pipeline live at the PROJECT ROOT
  (like `visualize.ipynb`), not in `reports/`. `nbconvert --execute` runs the
  kernel with cwd = the notebook's folder, which breaks `from flow import flow` and
  the relative `data/` paths for a notebook in a subdir; at the root, cwd = the
  project root and both resolve. `reports/render/` holds the rendered HTML. Updated
  the "Render / publish a notebook" section (nbconvert paths now root-relative),
  the "Publish a report" bullet, and the floor `CLAUDE.md`; rationale in
  `design-notes.md`.
- Validated the code-organization convention by applying it to a real project
  (executed, not paper). Outcomes folded in: the shared-helper rule is now
  concept-by-default (an earlier DAG-topology rule had zero real instances of its
  "chain -> upstream module" branch); `eda/` is read-only (code that writes a
  `data/` artifact is an external-derived source task or a hand-curated maintenance
  script, not a probe); filenames drop the redundant subject token
  (`verify_coercion.py`, not `verify_dataoews.py`); snake_case is anchored by a
  `# task: <Class>` header (case-splitting alone mis-converts `EmploymentbyMSA`);
  a probe spanning two subjects with no clear primary goes under a shared concept
  folder (`eda/geo/`); graduating a root module into `viz/` is a move, not a copy;
  and the import contract is documented (resolves only via `python -m` from root;
  a package `__init__.py` must not import a task at load).

## [26.5.30.3] - 2026-05-30

### Added
- Notebook publish/render now triggers the skill: added publish / render /
  export-to-HTML (jupyter nbconvert) and re-execute-to-refresh to the skill
  `description` and `when_to_use` frontmatter. Without these the skill did not
  auto-activate on "publish the notebook", so its render guidance never entered
  context and the agent improvised a flagless nbconvert command. This is the fix
  for the documented "Render / publish a notebook" section not taking effect.
- Notebook render/publish workflow: documented how to refresh a report
  notebook's outputs in place (`jupyter nbconvert --to notebook --execute
  --inplace reports/<name>.ipynb`) and publish it to standalone HTML
  (`jupyter nbconvert reports/<name>.ipynb --to html --output-dir reports/render
  --no-input --no-prompt --template classic`), run from the project root. The
  `--no-input` / `--no-prompt` / `--template classic` flags are called out as
  REQUIRED (they strip code cells / prompt numbers for a clean report) so they do
  not get dropped, and `--output-dir` is preferred over `--output` (whose path is
  relative to the input notebook). New "Render / publish a notebook" section in SKILL.md, plus a
  "Publish a report" bullet in Workflow Operations.
- Template now ships `reports/` (version controlled) and `reports/render/`
  (gitignored, for rendered output) with `.gitkeep` files, matching the layout
  the skill documents. These are plugin-specific additions on top of the
  vendored template (like `CLAUDE.md` / the data-doc skeleton); fold them back
  into the `oryxflow-template-minimal` source repo on the next sync.
- Iterate-then-run across parameter variants: a code edit invalidates EVERY
  cached instance of a task (one per parameter value), but a reset/run only
  recomputes the variant you actually run - so loading another variant later
  yields the stale schema (e.g. `KeyError` on a newly added column). Documented
  the `oryxflow.runLoad(Task, params=..., reset=True)` fix to force a recompute
  per setting (SKILL.md "Modify an existing task").
- Reading the Execution Summary: after a run, the summary's "complete ones were
  encountered" (cache hits) vs "ran successfully" (recomputed) lines are how you
  confirm a reset took effect, not just that the run succeeded. Captured in
  SKILL.md "Debug workflow issues".
- Reset-as-commented-toggle pattern: keep `flow.reset(...)` lines in `run.py` as
  commented-out toggles (one task per line; uncomment one or several to reset,
  re-comment after) rather than deleting them - the standing list of reset-ables
  is the intended pattern. Captured in SKILL.md ("Workflow Operations" and
  "Modify an existing task"). The same toggle discipline applies to
  `flow_params.py`: keep frequently-switched or being-compared settings as
  commented-out alternatives and toggle by commenting/uncommenting rather than
  rewriting the value (SKILL.md "Change parameters").
- Run-EDA-as-a-module rule: EDA scripts import project modules
  (`from flow import flow`), so they must run as `python -m eda.<name>` from the
  project root, NOT `python eda/<name>.py` (which puts `eda/` on `sys.path`
  instead of the root, breaking `import flow` / `import tasks`). The skill also
  forbids patching `sys.path` to work around it. Corrects the prior guidance in
  SKILL.md ("Workflow Operations") that said to run `python eda/<name>.py`
  directly.

### Changed
- Tightened and reorganized `SKILL.md` (~27% smaller: 486 -> 358 lines) with no
  behavior change. The orientation material was the bloat - the PLACEHOLDER rule
  was explained three times and task-naming four times; these are now stated
  once, with pointers ("see Naming tasks", etc.) elsewhere. The plain-invocation
  flow is a numbered decision procedure rather than repeated prose, and the
  "Project Documentation to Maintain" section was merged into "Session Start"
  (the code-is-source-of-truth story is now stated once). Every do/do-NOT rule
  and code example is preserved. Rationale in `docs/design/design-notes.md` is
  unchanged (two-tier split, orient-from-code, unified marker all still hold).
- Trimmed redundancy in `reference.md`: the "define once, import everywhere"
  rationale was stated three times (collapsed the `flow.py` and `flow_params.py`
  best-practice blocks to point at "How the Files Work Together"), and the
  duplicate docstring guidance + example under "Error Handling & Documentation"
  now defers to the "Task Design" best practice.

## [26.5.30.2] - 2026-05-30

### Added
- Run-from-working-directory rule: the shell already starts in the project root,
  so run `python run.py` / `python eda/<name>.py` directly - do NOT prepend
  `cd <project path>` (redundant, and brittle when the path has spaces).
  Captured in SKILL.md ("Workflow Operations").
- On-orientation discoverability: the skill now ENDS every orientation (built
  pipeline or fresh scaffold) by surfacing a short, grouped set of example
  invocations (Build / Run / Inspect / Understand), since in-session is the only
  place a user sees how to invoke it (README is not visible mid-session,
  `argument-hint` only shows `[explore]`). Also handles "what can I do here?" /
  "how do I use this" / "help" by listing them, and points to the README's
  "Things you can ask" as the fuller reference. New "Example invocations to
  offer" block in SKILL.md, referenced from both orientation paths.
- EDA-before-task guidance: before creating a data-loading task it is fine (not
  required) to write throwaway EDA code under `eda/` to figure out the source;
  otherwise just write the task and iterate by running it. The actual load still
  lands in the task, never in `eda/`. Captured in SKILL.md ("Naming tasks").
- Docstring standard (since pipeline docs live in the code): a task docstring IS
  its documentation - state purpose + input/output contract + quirks, do NOT
  restate the `run()` code or settle for a one-line "brief description". Same for
  the `tasks.py` module docstring and the data doc. Captured in SKILL.md ("Task
  docstrings"), the "Add a new task" example now models it, and reference.md's
  task-design best practices were aligned (also fixing a stale "name tasks with
  verbs" bullet that contradicted the output-naming convention).
- Task-naming convention: name a task for the OUTPUT it produces (a noun, e.g.
  `OEWSWages` / `DataOEWS`), not the verb it performs; avoid generic
  `GetData` / `LoadData` / `Process`. A plain-language "load the X data" request
  is treated as "create a new output-named task" - and the scaffold's
  `GetData` / `Process` are placeholder names to REPLACE, never to write real
  logic into. Captured in SKILL.md ("Naming tasks", "Add a new task", scaffold
  + onboarding notes) and reference.md.
- Iterate-then-run guidance for the common data-science loop: oryxflow caches by
  task identity (class + params), so PARAMETER changes auto-detect but CODE edits
  do NOT - an edited-but-unreset task is silently skipped on the next run. The
  skill now mandates `flow.reset(<EditedTask>)` (which cascades downstream)
  before running an edited task, and treats "edited a task, now run the flow" as
  reset-then-run. Captured in SKILL.md ("Modify an existing task") and reference.md.
- `docs/design/architecture.md` - a system map for developers (human or Claude):
  component table, the three interacting artifacts, load tiers, control/data
  flows, invariants, and a "where to change X" playbook. Linked as read-first
  from the root `CLAUDE.md`. Moved `design-notes.md` into `docs/design/`
  alongside it (rationale companion to the map).
- Fresh-scaffold onboarding now surfaces a couple of plain-language example
  requests ("run the flow", "explore the data", etc.) so a first-time user
  learns how to drive the skill. Mirrored as a "Things you can ask" list in
  `README.md` under "Using the skill". The examples lead with the most common
  build action - adding a new task wired to an upstream via `@oryxflow.requires`
  - and the README list adds the root-task and multiple-input variants.
- `when_to_use` frontmatter on the skill, carrying the invocation trigger
  phrases (create/modify task, run/preview the flow, re-run/reset, load/plot
  output, explore the data, summarize the pipeline) - the documented home for
  example invocations, used for auto-activation discovery.
- `argument-hint: [explore]` on the skill so the `explore` deep-dive argument
  shows during autocomplete.
- Top-level `description` in `marketplace.json` (was missing; the marketplace
  listing showed a blank line for it).
- `README.md` "Resources" section linking the upstream oryxflow docs / source for
  the invoking user, with a placeholder note that the plugin's own public repo /
  `homepage` / `repository` links will go there once the repo is public.

### Changed
- Changelog workflow: dropped the `[Unreleased]` bucket. The top section is now
  the current working version (matching `plugin.json` `version`); bullets are
  added there directly as work happens. Release docs in `CLAUDE.md` and `README`
  updated to match.
- Owner/author is now `d6t` / `dev@databolt.tech` (was `Oryx Intel` /
  `dev@oryxintel.com`) in both manifests; added `homepage: https://databolt.tech`
  to `plugin.json` and a "Maintainer" link in the README "Resources" section.
- Removed all "Luigi" references (manifests, README, SKILL.md, reference.md,
  template `CLAUDE.md`, architecture notes, and the `luigi` keyword) - oryxflow is
  described on its own terms now.
- Aligned every oryxflow description (both manifests, README intro, SKILL.md
  body + frontmatter, reference.md) to the library's official framing: "build
  highly effective data science workflows ... chain complex parameterized data
  flows, cache intermediate results, rerun intelligently, build better models
  faster" (was generic "reproducible data pipelines").
- Tightened the skill `description` (what it does + core trigger) now that
  `when_to_use` carries the example requests; the two share a 1,536-char cap.
- Skill body notes that `/oryxflow` / `/oryxflow explore` are shorthand for the
  real `/oryxflow:oryxflow [explore]` invocation form.
- `commands/project-init.md` is now `disable-model-invocation: true` - the
  scaffold writes files, so it is manual-trigger only (type the command), not
  auto-invoked. README "Using the skill" notes this.

## [26.5.30.1] - 2026-05-30

Plugin-first documentation model and a project scaffolding command.

### Added
- `/oryxflow:project-init` (`commands/project-init.md`) - scaffolds a new project
  by shell-copying the bundled template into the current directory,
  skip-existing / never-overwrite.
- `resources/template-minimal/` - vendored mirror of the `oryxflow-template-minimal`
  repo (the scaffold source), plus plugin-specific additions: a compact
  self-contained project `CLAUDE.md`, a `PLACEHOLDER` data-doc skeleton
  (`docs/oryxflow-data.md`), placeholder module + task docstrings in `tasks.py`,
  and `.creds.yaml.example`.
- `skills/oryxflow/ml-patterns.md` - on-demand ML pipeline task templates (feature
  engineering, model training, SHAP, expanding-window backtest), harvested from
  the former `docs/claude-oryxflow-ml.md`.

### Changed
- Adopted an in-code-first documentation model: pipeline meaning lives in the
  code (a `tasks.py` module docstring for the goal, per-task docstrings, and the
  `@oryxflow.requires(...)` graph / `flow.preview()`), so there is no separate
  pipeline doc to drift. Only data findings - which have no code home - keep a
  file, `docs/oryxflow-data.md` (was `claude-data-doc.md`).
- Unified the `PLACEHOLDER` marker across code AND the data doc: a marker means
  "not real yet" everywhere, replacing the old "docs absence = explore" signal.
- `SKILL.md` now orients from code + the data doc instead of carrying inline doc
  templates, and drops the old `claude-project.md` references.
- `docs/design-notes.md` documents the three-layer model (plugin knowledge /
  in-code + data-doc project docs / always-on `CLAUDE.md`), the unified marker,
  and the init + vendored-mirror approach.

### Removed
- Legacy generic docs `docs/claude-project.md`, `docs/claude-data-doc.md`,
  `docs/claude-ml-plan.md`, `docs/claude-oryxflow-ml.md` (redundant with the
  plugin's reference/ml-patterns, or superseded by the model above).

## [26.5.30] - 2026-05-30

Initial packaging of the standalone `oryxflow` skill into a versioned plugin.

### Added
- Plugin manifest (`.claude-plugin/plugin.json`) and self-marketplace
  (`.claude-plugin/marketplace.json`) so the repo is installable from git or a
  local path.
- `skills/oryxflow/SKILL.md` and `skills/oryxflow/reference.md` (copied from the
  pre-plugin skill at `~/.claude/skills/oryxflow`).
- `README.md` (install + dev instructions), `CLAUDE.md` (plugin-development
  guide), `docs/design-notes.md` (design rationale), `.gitignore`.

### Skill behavior captured in this version
- Session-start orientation protocol: read the per-project docs first, treat
  them as a cache, and avoid re-scanning what is already recorded.
- Lightweight default invocation; deep exploration is opt-in
  (`/oryxflow explore` or a plain-language request).
- `PLACEHOLDER SCAFFOLD` marker convention for recognizing fresh scaffolds.
- Raw source data lives in `data/` (`.csv` / `.xlsx`); task outputs are parquet
  under per-task subfolders.
- Fresh-scaffold orientation on a plain `/oryxflow` invocation gives friendly
  onboarding rather than narrating the placeholder internals: it confirms the
  project is a fresh scaffold, points the user at how to create tasks, load
  data, and run the flow, then offers the two next steps (explore vs. describe
  the goal).

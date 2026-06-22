# Changelog

All notable changes to the d6tflow plugin are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions are
date-based (`YY.M.D`, e.g. `26.5.30`).

## [26.6.22] - 2026-06-22

### Added
- New `/d6tflow:init-gitlfs` command (`commands/init-gitlfs.md`) - puts a
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
- Report notebooks are now template-based. The scaffold ships the notebook as
  `viz-template.ipynb` (was `visualize.ipynb`); the convention is one-report-per-
  notebook - copy the template to a subject-named `viz-<topic>.ipynb` at the root
  and edit the copy, never the template in place (which a session had done,
  consuming it and tying one report to the generic name). `--output-dir` then
  renders `reports/render/viz-<topic>.html` for free. Renamed the template file and
  updated all references (`SKILL.md`, `reference.md`, template `CLAUDE.md`,
  `init-project.md`, root `CLAUDE.md`, architecture, design-notes). `visualize.py`
  is unchanged - it has a different lifecycle (graduates into `viz/<subject>.py`).
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
- Task docstrings no longer carry "see `docs/d6tflow-data.md`" cross-references.
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
  re-synced from a separate `d6tflow-template-minimal` source repo. Updated
  `CLAUDE.md`, `architecture.md`, and `design-notes.md` accordingly.
- Broadened skill activation triggers in `SKILL.md` frontmatter: `description`
  and `when_to_use` now name loading / cleaning / transforming / analyzing data
  (each phrased as "becomes a task"), so plain-language data-prep requests like
  "clean the data" reliably auto-activate the skill from a cold context, not only
  task/flow-shaped phrasings. No behavior change once active.
- Renamed `/d6tflow:project-init` to `/d6tflow:init-project`
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
  quality issues, business rules) get promoted into `docs/d6tflow-data.md`. An
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
  into the `d6tflow-template-minimal` source repo on the next sync.
- Iterate-then-run across parameter variants: a code edit invalidates EVERY
  cached instance of a task (one per parameter value), but a reset/run only
  recomputes the variant you actually run - so loading another variant later
  yields the stale schema (e.g. `KeyError` on a newly added column). Documented
  the `d6tflow.runLoad(Task, params=..., reset=True)` fix to force a recompute
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
- Iterate-then-run guidance for the common data-science loop: d6tflow caches by
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
  build action - adding a new task wired to an upstream via `@d6tflow.requires`
  - and the README list adds the root-task and multiple-input variants.
- `when_to_use` frontmatter on the skill, carrying the invocation trigger
  phrases (create/modify task, run/preview the flow, re-run/reset, load/plot
  output, explore the data, summarize the pipeline) - the documented home for
  example invocations, used for auto-activation discovery.
- `argument-hint: [explore]` on the skill so the `explore` deep-dive argument
  shows during autocomplete.
- Top-level `description` in `marketplace.json` (was missing; the marketplace
  listing showed a blank line for it).
- `README.md` "Resources" section linking the upstream d6tflow docs / source for
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
  template `CLAUDE.md`, architecture notes, and the `luigi` keyword) - d6tflow is
  described on its own terms now.
- Aligned every d6tflow description (both manifests, README intro, SKILL.md
  body + frontmatter, reference.md) to the library's official framing: "build
  highly effective data science workflows ... chain complex parameterized data
  flows, cache intermediate results, rerun intelligently, build better models
  faster" (was generic "reproducible data pipelines").
- Tightened the skill `description` (what it does + core trigger) now that
  `when_to_use` carries the example requests; the two share a 1,536-char cap.
- Skill body notes that `/d6tflow` / `/d6tflow explore` are shorthand for the
  real `/d6tflow:d6tflow [explore]` invocation form.
- `commands/project-init.md` is now `disable-model-invocation: true` - the
  scaffold writes files, so it is manual-trigger only (type the command), not
  auto-invoked. README "Using the skill" notes this.

## [26.5.30.1] - 2026-05-30

Plugin-first documentation model and a project scaffolding command.

### Added
- `/d6tflow:project-init` (`commands/project-init.md`) - scaffolds a new project
  by shell-copying the bundled template into the current directory,
  skip-existing / never-overwrite.
- `resources/template-minimal/` - vendored mirror of the `d6tflow-template-minimal`
  repo (the scaffold source), plus plugin-specific additions: a compact
  self-contained project `CLAUDE.md`, a `PLACEHOLDER` data-doc skeleton
  (`docs/d6tflow-data.md`), placeholder module + task docstrings in `tasks.py`,
  and `.creds.yaml.example`.
- `skills/d6tflow/ml-patterns.md` - on-demand ML pipeline task templates (feature
  engineering, model training, SHAP, expanding-window backtest), harvested from
  the former `docs/claude-d6tflow-ml.md`.

### Changed
- Adopted an in-code-first documentation model: pipeline meaning lives in the
  code (a `tasks.py` module docstring for the goal, per-task docstrings, and the
  `@d6tflow.requires(...)` graph / `flow.preview()`), so there is no separate
  pipeline doc to drift. Only data findings - which have no code home - keep a
  file, `docs/d6tflow-data.md` (was `claude-data-doc.md`).
- Unified the `PLACEHOLDER` marker across code AND the data doc: a marker means
  "not real yet" everywhere, replacing the old "docs absence = explore" signal.
- `SKILL.md` now orients from code + the data doc instead of carrying inline doc
  templates, and drops the old `claude-project.md` references.
- `docs/design-notes.md` documents the three-layer model (plugin knowledge /
  in-code + data-doc project docs / always-on `CLAUDE.md`), the unified marker,
  and the init + vendored-mirror approach.

### Removed
- Legacy generic docs `docs/claude-project.md`, `docs/claude-data-doc.md`,
  `docs/claude-ml-plan.md`, `docs/claude-d6tflow-ml.md` (redundant with the
  plugin's reference/ml-patterns, or superseded by the model above).

## [26.5.30] - 2026-05-30

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
- Fresh-scaffold orientation on a plain `/d6tflow` invocation gives friendly
  onboarding rather than narrating the placeholder internals: it confirms the
  project is a fresh scaffold, points the user at how to create tasks, load
  data, and run the flow, then offers the two next steps (explore vs. describe
  the goal).

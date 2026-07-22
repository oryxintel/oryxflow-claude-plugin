# Plan: Experiment-management guidance for the oryxflow skill

## Context

A oryxflow data-science project today is documented well for the *single-run*
and *prod* lifecycle, but the **experiment** lifecycle - exploring many
parameter combinations, tracking what was tried, comparing results, and
documenting outcomes - is essentially undocumented in the skill. Concretely:

- `WorkflowMulti` appears exactly once (reference.md), `params_generator_single`
  / `params_generator_df` / `generate_exps_for_multi_param` appear nowhere, and
  only `params_generator_dictlist` is shown, with no explanation of the four
  generators' different shapes.
- There is **no** guidance on tracking which variant ran, comparing metrics
  across variants, documenting outcomes, or keeping experiment work from
  polluting prod cache/data.

This work fills that gap **in the skill docs** (the plugin's artifact), so an
agent driving a real oryxflow project runs sweeps the house way: native oryxflow
tooling, results captured as artifacts, outcomes written down.

Decisions locked with the user:
- **Skill docs are the deliverable.** New on-demand `experiments.md`, plus small
  touch-ups to `reference.md`, `ml-patterns.md`, `SKILL.md`. The default
  `template-minimal` scaffold is **not** changed; experiments.md teaches by a
  complete inline worked example. (An opt-in reference-implementation example
  under `resources/` is noted as a possible follow-up, not built now.)
- **Skip Weights & Biases entirely.** Native oryxflow only - no external
  dependency, no API-key auth in the default workflow. (A W&B MCP server exists
  and works with Claude Code; deliberately out of scope to keep the template
  dependency-free.)
- **Code/data strategy: env-segregation by default, branches by scale** (see the
  recommendation in experiments.md content below).

## What oryxflow already gives us (verified against the installed lib)

`oryxflow/__init__.py` and `oryxflow/utils.py` (installed at
`/path/to/oryxflow/oryxflow`):

- `oryxflow.WorkflowMulti(task, params, path=None, env=None)` - many flows, one
  per param set. `params` accepts a dict-of-lists (auto cartesian), a list, or a
  dict-of-dicts (named flows).
- `wm.run(flow=None)` runs ALL flows -> `{flow_key: RunResult}`; `flow=key` runs
  one. `wm.outputLoad(task, flow=None)` -> `{flow_key: output}`; `flow=key` ->
  single. `wm.reset(task, flow=key)`, `wm.preview(...)` mirror this.
- `oryxflow.utils` generators, all returning `{key: params_dict}` for
  WorkflowMulti:
  - `params_generator_single(dict_, params_base=None)` - sweep ONE param.
  - `params_generator_dictlist(params_dict, params_base=None)` - full cartesian
    GRID of several params (numeric keys).
  - `params_generator_df(df, params_base=None)` - one experiment per DataFrame
    ROW (irregular combos, not a full grid).
  - `generate_exps_for_multi_param` (alias `params_generator_multiple`) - like
    the grid but keys are descriptive flow names (e.g. `dropout_0.1_model_lstm`).
- **No native metric tracking / comparison** - aggregation is manual (this is
  exactly the pattern experiments.md must supply).

## Files to change

### 1. NEW: `skills/oryxflow/experiments.md` (on-demand, ASCII, ~78-col wrap)

The primary deliverable. Sections:

1. **When to reach for this** - you are comparing >1 parameter setting / doing a
   sweep / want to track outcomes. One run -> stay with `flow`; many -> this.
1b. **The organizing principle: parameterize what you intend to compare.** Stated
   up front - it is the spine that ties sweeps, rollback, and git together.
   Express the thing you will compare as a PARAMETER (model choice ->
   `ChoiceParameter`; a dataset / feature-set -> `BoolParameter` gate; a
   hyperparam -> numeric `Parameter`). Once it is a param: comparison is a native
   WorkflowMulti sweep, variants COEXIST in cache (no overwrite), expensive
   upstreams are REUSED (toggling resets only downstream), and "rollback" becomes
   "set back to default / do not promote" - NEVER a code revert. Code edits (and
   maybe a branch) are the FALLBACK for what cannot be parameterized. Decision
   tree the whole doc hangs on:
   - *Can this difference be a parameter?* YES -> add a param, sweep it, no
     branch. NO (new libs, structurally different task body) -> edit code; if
     speculative / might-roll-back -> branch (point 7).
   - Keep knobs INDEPENDENT (one param per concern) so a partial rollback
     ("rolled MOST of it back") is setting one param back to default, not
     untangling a commit.
2. **Define the sweep with the right generator.** Brief decision rule + one tiny
   example each: `params_generator_single` (one axis), `params_generator_dictlist`
   (full grid), `params_generator_df` (hand-picked rows), `generate_exps_for_multi_param`
   (named flows). All feed WorkflowMulti; all merge a shared `params_base`.
3. **Run + load across variants.** `wm = oryxflow.WorkflowMulti(FinalTask,
   params=...)`; `wm.run()` -> dict of RunResult; `wm.outputLoad(Task)` ->
   dict keyed by flow; per-flow `flow=key`; per-flow `reset`.
4. **Track metrics natively (no external tracker).** PREREQUISITE, state it
   first: you can only compare what the swept leaf task EMITS - if it saves only
   a model object, there is nothing to aggregate. Each experiment task
   `self.saveMeta({'rmse': ..., 'auc': ...})` (or saves a one-row metric frame);
   then an aggregation/compare task loops the flows, pulls
   `wm.outputLoadMeta(Task)` / `wm.outputLoad(Task)`, and builds a comparison
   DataFrame (one row per param set, columns = params + metrics). Full worked
   code block - this is the canonical "compare runs" pattern.
5. **Document outcomes.** Commit the comparison table as an artifact under
   `reports/` (xlsx/csv) AND keep a human log `docs/experiments.md`: a markdown
   table of date / param set / headline metric / verdict-decision, plus enough
   to REPRODUCE the row (param set + date, and the git commit when the code
   varied) - that traceability is what makes a later promotion (point 6)
   defensible. The log is the "why we picked this", the table is the numbers.
6. **Experiment vs prod data, and the promotion path.** Built on a verified
   mechanic: `env` only appends `/env={env}` to the OUTPUT PATH - it does NOT
   change `task_id`. So two layers do two different jobs, and the doc must keep
   them distinct:
   - **Parameters separate sweep variants from each other.** Each param combo
     already gets its own cache slot (distinct `task_id`) - that is what
     WorkflowMulti relies on. You do NOT need a separate env to keep variants
     apart; do NOT reach for env to do params' job.
   - **`env` separates experiment storage from PROD storage.** Research IS
     experimentation, so experiments live in the existing dev/default env (the
     same place research already runs - per the established dev-vs-prod model in
     ml-patterns.md). Do NOT invent a third `env='experiment'`; that conflicts
     with the documented two-env convention. The payoff of the split: prod
     artifacts are insulated from experiment churn (a code edit while
     experimenting invalidates dev-env variants, not the frozen `data/prod/`
     tree), and you can wipe ALL experiment outputs by clearing the dev-env
     subtree without touching prod. OPTIONAL: give a big throwaway experiment
     campaign its OWN env label (e.g. `env='exp_<topic>'`) purely so it can be
     deleted wholesale - an option, not the default.
   - **Promotion is a params copy, NOT a data copy.** Winning params graduate
     into `params_prod` in `flow_params.py`; the first prod run then RECOMPUTES
     under `env='prod'` (cold - dev-env artifacts are at a different path, so
     they are not reused) against fresh data, training the prod model once;
     later periodic refreshes reuse that frozen model. Because the win is only
     reproducible if its code + params are recorded, promotion couples to the
     experiments log (point 5) - the log row is what makes a promoted number
     traceable back to the run that produced it.
   - Cross-link ml-patterns.md "Productionizing" (this doc is the explore-many
     front end; that section is the freeze-and-promote back end).
7. **Code/data + git (the recommendation), corrected for what git can isolate.**
   Key fact: `data/` is gitignored, so switching branches leaves cached outputs
   untouched - **git branches CANNOT isolate experiment data; only env/params
   can, on any branch.** Therefore a branch buys exactly ONE thing: isolating
   experiment CODE. The recommendation:
   - **Default - no branch.** Routine sweeps change only PARAMS, not code, so
     there is nothing to isolate: define named experiment param sets in
     `flow_params.py`, run on the current branch, env/params keep the data
     separate. Branching here is pure overhead.
   - **Branch only for speculative CODE.** You only land here AFTER the point-1b
     decision said the difference cannot be a parameter. When an experiment needs
     task-code changes you do not want on main yet (new feature engineering, a
     reworked model, a new task), use a branch and merge the winner back.
     Size/longevity follows from that, but the trigger is "must this be a code
     change (not a param)?", not "is this a big experiment?".
   - **Commit the durable record, never the cache.** Commit experiment code +
     the small RESULT summaries (comparison table under `reports/`, the
     `docs/experiments.md` log); never commit `data/` (gitignored, regenerable).
     The log + table belong on `main` even when the code experiment was branched
     (merge them back) - they are the record that outlives the branch.
   - **Prune concluded experiments.** Once an experiment concludes, delete its
     param-set definition from `flow_params.py` - the log + comparison table
     preserve the record, so flow_params.py does not accumulate dead variants. A
     project running MANY experiments graduates to a dedicated experiments module
     (a "scaling up" nudge), same as the tasks.py-split path.
8. **Execution layer convention.** Drive sweeps from a `run_experiments.py` at
   the project root (parallel to `run.py`) - keeps the no-inline-Python rule;
   the aggregation lives in a task, not the script.
9. **Identity gotchas (cross-link, do not re-explain).** Never sweep a
   `significant=False` param (variants collide on one cache slot). A code edit
   invalidates every variant but only run ones recompute - see SKILL.md "Across
   parameter variants". Keep this short, point to SKILL.md.
10. **Lifecycle coverage - the four canonical DS cases (close the doc with a
   compact walkthrough, each mapping to sections above; this is the
   stress-test).** The arc: EXPLORE (eda/) -> decide param-or-code (1b) -> SWEEP
   (2-3) + AGGREGATE (4) -> DECIDE/log (5) -> promote or roll back (6-7) ->
   prune (7).
   - **Compare model HYPERPARAMS** (the clean case): grid via
     `params_generator_dictlist` over numeric Parameters -> sweep -> compare
     table. Leaf must emit a metric (4). No code edit, no branch.
   - **Compare different MODELS, then roll back** ("tried a new model, it lost"):
     STEER to a `ChoiceParameter` (`model='rf'|'xgb'`) -> it becomes the
     hyperparam case; both outputs coexist, rollback = do not promote, nothing to
     revert. Only if the new model needs structural code (different libs/prep)
     does it fall to code-edit + branch (7) - and note the friction it avoids:
     editing rf->xgb in place keeps the same `task_id`, so xgb OVERWRITES rf's
     cached artifact and rollback forces a reset+recompute.
   - **EDA before trying a model** ("where does all that code go?"): NOT here - it
     goes in `eda/<subject>/*.py` probes (findings -> `docs/oryxflow-data.md`),
     scratch in `data/.eda/`. Cross-link the existing SKILL.md EDA conventions.
     The boundary: a probe writes no pipeline artifact; a probe that proves out
     GRADUATES into a feature task, which then enters the sweep as a param.
   - **Add a NEW DATASET** (ingest/clean/feature changes throughout): gate it
     behind a `BoolParameter` (`use_<dataset>=False`) in the feature task -> the
     with/without question becomes a native sweep; the expensive ingest is a
     separate upstream task cached ONCE (toggling resets only downstream);
     "didn't help" = leave the toggle False, code dormant, no revert. Do the
     messy build on a branch (lots of speculative code, per 7) AND param-gate it,
     so the merged winner stays toggleable. This case exercises 1b + 6 + 7
     together and is the doc's hardest worked example.

### 2. `skills/oryxflow/reference.md` - API surface only

Around the existing WorkflowMulti block (~lines 356-371): replace the single
`params_generator_dictlist` example with a compact catalog of **all four**
generators (one line each: input shape -> output) and the WorkflowMulti method
semantics (`run`/`outputLoad`/`reset` return dicts keyed by flow; `flow=`
selects one). Keep it terse - reference is the API catalog; the how-to-run-an-
experiment narrative lives in experiments.md. End with a pointer to experiments.md.

### 3. `skills/oryxflow/ml-patterns.md` - cross-link

In "Productionizing: prod vs experiment" (~line 403): add one sentence pointing
forward to experiments.md for the explore-many / sweep / compare front end, so
the two halves of the lifecycle reference each other.

### 4. `skills/oryxflow/SKILL.md` - lean pointers only (guard against bloat)

- Depth-on-demand paragraph (lines 39-45): add `experiments.md` with a 6-8 word
  gloss ("running parameter sweeps, comparing + documenting experiment runs").
- Additional Resources list (lines 619-623): add the experiments.md line.
- Example invocations (line 113 "Run" group): add "run a parameter sweep /
  compare variants".
- Graduation nudges (lines 161-167): add one trigger line - "comparing many
  param variants by hand -> offer a WorkflowMulti sweep + an experiments log".
  One line; no more.

### 5. Design docs + changelog (repo conventions require this)

- `docs/design/architecture.md` component table: add the `experiments.md` row
  (on-demand tier, "parameter sweeps, run tracking, comparison, experiment-vs-
  prod data + git strategy").
- `docs/design/design-notes.md`: short note on the two non-obvious calls -
  (a) native-tracking, NOT W&B (keep template dependency-free; W&B MCP exists
  but is opt-in/out-of-scope); (b) env-segregation default + branch-by-scale for
  experiment/prod coexistence.
- `docs/CHANGELOG.md`: bullet under the top section's `### Added`
  ("experiments.md: parameter sweeps with WorkflowMulti, native run tracking +
  comparison, experiment vs prod data/git strategy").
- `.claude-plugin/plugin.json`: bump `version` to match the changelog top
  section (per repo release rule - a new doc that consumers should pull is a
  clean cut; use today's date `YY.M.D`, matching the changelog heading).

## Explicitly NOT doing

- No Weights & Biases content anywhere.
- No changes to `resources/template-minimal/` (scaffold stays as-is). A possible
  follow-up: an opt-in `resources/examples/` reference implementation the skill
  could point to - flagged, not built now.
- No new oryxflow library code - we only document existing APIs.

## Verification

This is documentation, so verification is correctness + load-behavior, not a
test suite:

0. **Load-bearing mechanics behind sections 6-7 (verified, keep true in prose):**
   `env` only appends `/env={env}` to the output path and does NOT change
   `task_id` (confirmed: `Workflow.__init__` injects `path`, which is not a class
   param / not part of identity) - so "params separate variants, env separates
   storage" must read exactly that way. And `data/` is gitignored in the template
   - so "branches isolate code, not data" must stay phrased as a correction, not
   a suggestion. If a future lib change alters either fact, the wording changes.
1. **API claims are real** (already spot-checked, re-confirm after drafting):
   from the repo, inspect the installed lib for each name used -
   `python -c "import oryxflow, oryxflow.utils; print([n for n in
   ('WorkflowMulti',) if hasattr(oryxflow,n)],
   [n for n in ('params_generator_single','params_generator_dictlist',
   'params_generator_df','generate_exps_for_multi_param') if
   hasattr(oryxflow.utils,n)])"` and confirm `WorkflowMulti.outputLoad` /
   `.run` signatures match what experiments.md shows. Every code block in
   experiments.md must use only verified names/signatures.
2. **Plugin still valid**: `claude plugin validate .` (checks plugin.json +
   marketplace.json after the version bump).
3. **Load-tier discipline**: confirm SKILL.md grew only by the few pointer lines
   (no narrative bloat) and that the sweep how-to lives in experiments.md, the
   API catalog in reference.md (no duplication between them).
4. **ASCII + wrap**: grep the new/edited files for non-ASCII; confirm ~78-col
   wrap, matching the existing skill files.
5. **Cross-links resolve**: experiments.md <-> ml-patterns.md "Productionizing"
   and <-> SKILL.md "Across parameter variants" point at text that exists.

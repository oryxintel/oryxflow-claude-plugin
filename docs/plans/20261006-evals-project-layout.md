# Evals in any repo: the `evals/` project, the probe tier, docs first

> Depends on the library half in the oryxflow repo:
> `docs/todo/20261006-evals-release-readiness.md` (outputs/scores split, `baseline=`,
> `side_by_side()`, launch guard, pydantic-evals >= 2, PyPI release). Do not release this plan's
> changes before `oryxflow[evals]` with those features is on PyPI - the commands install and call it.

## Context

The four `eval-*` commands, `template-eval/` and `evals.md` were written against an oryxflow data
project. The first consumer that needs evals most is not one: a downstream consumer project (an LLM
web app, Python package in a `backend/` subdirectory, credentials loaded by a tool that resolves
relative to the working directory). Reading its evals and ~25 throwaway probe scripts showed:

- **Five evals, five layouts.** Each re-implements path and credential setup; one runs only from
  `backend/`, and run from the repo root it "succeeds" with no credentials and empty results.
- **Probes instead of evals.** Plans carried well-designed real-model probes (arms, controls, pass
  bars) as gitignored `tmp/probe_*.py`, deleted after the decision. Placed outside the plan's tasks,
  a task-by-task executor never ran them; nothing re-checked a surface when it changed again.
- **Reinvented primitives.** Hand-built prompt-surgery arms, `git show` baselines, `asyncio.gather`
  runners, pydantic judges, exit-code gates and `*_outputs.md` side-by-sides - several of which
  `oryxflow.evals` or pydantic-evals already ship.
- **Fixed bars that got rewritten.** Absolute pass bars set before a run were missed, then
  rewritten as "B >= A". Results were mixed far more often than pass/fail.
- **The skill never fires there.** `oryxflow`'s description is data-science framed; an agent
  planning a router change in a web app never loads it.

Scope: the plugin and the library. The consumer project's own instructions are NOT changed by this
plan; it is used only to validate (the rule-capture dogfood run below).

## Decisions (signed off 2026-10-06)

1. **`evals/` is ONE oryxflow project; each eval is a folder inside it.**

   ```
   evals/                         # the project dir - always launch from here
     _env.py                      # once: credentials, import path to production code
     data/                        # one cache for every eval
     run_eval_rule_capture.py     # 3 lines: ev.cli(RuleCaptureEval)
     rule_capture/                # one eval (underscore: it is a Python package)
       __init__.py
       README.md                  # the plan (eval-plan)
       eval.py  agent.py
       cases.csv  fixtures/       # loaded relative to the module file, not cwd
       results/                   # verdicts + side-by-side, committed
   ```

   - One launch dir, one cache, setup written once - the consumer's real cost was setup duplicated
     per eval. Folder per eval because half an eval is hand-maintained non-code (plan, cases,
     fixtures, results) and you work on evals one at a time.
   - One `run_eval_<name>.py` per eval rather than one dispatcher: `ev.cli(Cls)` derives flags from
     one class's Parameters, so a dispatcher would need subcommands. Matches `run_prod.py` /
     `run_eda.py`.
   - Shared cache is safe because cells key on task class + params; eval classes must therefore be
     uniquely named (`RuleCaptureEval`, never `PromptEval`) - `eval-init` enforces it.
2. **Probe tier.** A probe is a single committed `evals/run_eval_<name>.py`: inline cases, `ev.sweep`,
   cached, results written to `evals/<name>/results/`. Same effort as `tmp/probe_*.py`; it survives
   and re-runs on the next change. It graduates to a `<name>/` folder (plan, `cases.csv`) when the
   cases are worth keeping.
3. **Docs first, for both libraries.** Before reading library source or guessing an API, fetch
   `https://docs.oryxflow.dev/llms.txt` (the LLM evals pages) and
   `https://pydantic.dev/docs/ai/evals/`. Source only to settle what the docs leave open; the
   INSTALLED version wins over the docs, and a mismatch gets reported.
4. **Reports need judgement, not pass/fail.** Bars in the plan are reference points. `eval-run`
   writes: the delta per arm against the baseline arm with its interval, what is inside noise, the
   trade-offs (one label up, another down is MIXED, not a win), and a recommendation with its
   reasons. No gate verdict, no verdict-derived exit code.
5. **Results are committed by default** - the verdict md and the side-by-side md
   (`EvalResult.side_by_side()`, Jinja-rendered, disagreeing cases first).
6. **Reach agents outside oryxflow projects two ways.** A small second skill, `oryxflow-evals`,
   triggered by planning or editing an LLM prompt, response schema, model choice or router input in
   any repo; and a copy-paste CLAUDE.md block in the README / docs for project specifics. The skill
   suggests, never invokes (the `eval-*` commands stay `disable-model-invocation: true`).

## Changes

1. **`resources/template-eval/`** -> the decision-1 layout: shared `_env.py` (PLACEHOLDER SCAFFOLD:
   credentials, sys.path), `run_eval_<name>.py`, `<name>/` package with `__init__.py`; cases and
   fixtures resolved from `pathlib.Path(__file__).parent`; `agent.py` imports `_env` first. Drop the
   per-eval `run_eval.py` and `ROOT = parents[2]`. Name the baseline arm (`baseline=`).
2. **`commands/eval-plan.md`** - `Running it` records the launch facts: where credentials come from
   and whether they need a specific cwd, where the production package lives and how it is imported.
   Q4: bars as reference points; the report is a judgement (decision 4). Add the docs-first step.
3. **`commands/eval-init.md`** - first run in a repo creates `evals/_env.py`, `evals/data/`
   (skip-existing), filling `_env.py` from the plan's launch facts; later runs add only
   `run_eval_<name>.py` + `<name>/`. Enforce a unique class name. Import probe runs from `evals/`.
   Install advice targets the `pyproject.toml` that owns the production package (may be a
   subdirectory) and pins `oryxflow[evals]>=<release>`.
4. **`commands/eval-run.md`** - run from `evals/`; write the side-by-side next to the verdict; the
   judgement report of decision 4.
5. **`commands/eval-cases.md`** - paths under the new layout.
6. **`skills/oryxflow/evals.md`** - docs-first rule; probe tier; a short "already in pydantic-evals"
   table (LLMJudge / GEval, ToolCorrectness / TrajectoryMatch / ArgumentCorrectness,
   ConfusionMatrixEvaluator, CaseLifecycle, generate_dataset); lessons from the probes: relative
   comparison against the control arm over fixed bars, never key a metric on labels the model itself
   writes (match on the quoted span), a fixture that names a state must be in it, credentials work
   in-process so an eval is not "blocked" on a dev server, record tool calls into the output.
7. **New `skills/oryxflow-evals/SKILL.md`** - tight description (it costs context in every session),
   body points at `evals.md` and the commands. Decide in implementation whether `evals.md` moves
   under it or is shared.
8. **README / docs** - install steps for library + plugin, the CLAUDE.md block, the layout.
9. **Bookkeeping** - `architecture.md`, `design-notes.md` (why one project, why probes are
   committed, why no hard gates), `CHANGELOG.md` `[Unreleased]`, this repo's `CLAUDE.md` layout
   section (`template-eval/` contents). `template-eval/` is not a floor file: no floor bump.

## Validation

1. **Fixture repo** - a throwaway app-shaped repo: package in a subdirectory, a credential loader
   that only works from one cwd. Run `eval-plan` -> `eval-init` -> smoke run; record every friction.
2. **Rule-capture dogfood in the consumer project** - build its missing eval with the four commands,
   without editing that project's instructions. Real cases already exist (rule-shaped user messages,
   a restated-rules history); deterministic metrics: precision of the new router flag, paraphrase
   groups merging to one key, flips in the router's OTHER flags against earlier boundary sets,
   pasted-text false positives. Baseline: the router before the field was added. Feed every friction
   back into this plan before release.
3. `/plugin validate .`, pre-commit hook green, ASCII-only check on all touched skill files.

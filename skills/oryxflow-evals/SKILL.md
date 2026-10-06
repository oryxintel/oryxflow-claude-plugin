---
name: oryxflow-evals
description: >-
  Measure whether an LLM prompt, response schema, model or router change is
  better, in any Python repo, with oryxflow.evals (cached arms, baselines from
  git, intervals). Use when planning or making such a change, when asked to
  eval, probe or A/B a prompt, or when working under an evals/ directory.
when_to_use: >-
  Trigger on: writing a plan or spec that changes a prompt / template / LLM
  output schema / model id / what a router or classifier reads; "is this prompt
  better?", "run a quick eval", "probe this", a prompt A/B; editing a prompt in a
  repo that has evals/; anything under evals/.
---

# Evaluating an LLM change with oryxflow.evals

A prompt change is a MEASUREMENT, not a read-through: one function under test x
cases x arms x repeats -> rates with intervals. The method - what to measure, the
mandatory guardrail, baselines, judges, reading a verdict - is in
[evals.md](evals.md). Load it before planning or writing an eval.

**Read the docs before the source.** https://docs.oryxflow.dev/llms.txt (the LLM
evals pages) and https://pydantic.dev/docs/ai/evals/ . pydantic-evals already ships
judges, tool-call checks and confusion matrices; reuse them. The INSTALLED version
wins over the docs. Install: `pip install "oryxflow[evals]>=26.10.5"`.

**A plan that changes LLM behavior names its eval.** Put the eval inside the
plan's TASKS, not in a "before merging" note - a step outside the task list is a
step a task-by-task executor never runs. Check `evals/` first: extending an
existing eval for that surface beats writing a new one. If the project's own
instructions make evals optional, say which eval you would run and why you are
skipping it, rather than leaving it out silently.

**A quick probe is a committed `evals/run_eval_<name>.py` using `ev.sweep`** - not
a gitignored `tmp/` script and not hand-rolled `asyncio`. Same length, cached, and
still there to re-run when the surface changes again. Run every eval from
`evals/`; `evals/_env.py` holds the repo's credentials and import path once.

**Edited a prompt in a repo with `evals/`? Say which arm went stale**, with the
bill: `/oryxflow:eval-run` re-runs it. A scorer or judge edit costs no model
calls - only the scoring re-runs.

**Suggest the commands; never invoke them** (two write files, one bills the
user): `/oryxflow:eval-plan` (decide what is measured, write the plan) ->
`/oryxflow:eval-init` (scaffold, 3-call smoke run) -> `/oryxflow:eval-cases` (grow
to 15-25 real cases) -> `/oryxflow:eval-run` (run, read side by side, judge).

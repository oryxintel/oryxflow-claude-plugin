# Evaluating an LLM prompt change (the method)

Loaded ON DEMAND by the `oryxflow-evals` skill ([SKILL.md](SKILL.md)) - pull this
in when the question is "I changed a prompt / template / model and I cannot tell
whether it is better", when a plan changes one, or when working inside `evals/`.
Needs `pip install "oryxflow[evals]>=26.10.5"` (pydantic-evals 2.x comes with it).

**Read the docs before the source.** For any API below, fetch
https://docs.oryxflow.dev/llms.txt (the LLM evals pages) and
https://pydantic.dev/docs/ai/evals/ first; open library source only to settle
what they leave open. The INSTALLED version wins over the docs - report a
mismatch. pydantic-evals already ships most per-case scoring (see "Reuse before
you write"), and an eval that re-implements it is the commonest waste.

The library does the arithmetic - rates, intervals, the paired delta, guardrail
marks, caching every cell so a re-run is free. This file is the part a library
cannot ship: **what to measure, and how to not fool yourself.** Nearly every rule
below is an observed failure in a real harness, not a hypothetical.

---

## The one idea

An eval is a COMPARISON, not a read-through. A script that fires ten turns and
prints them for a human to skim is not a measurement: no baseline, no metric, no
controls, nothing to re-run next month. The unit of work is

```
one function under test  x  N cases  x  M arms  x  R repeats  ->  a rate with an interval
```

and everything in this file exists to stop one of those four from lying to you.

---

## Where evals live: one `evals/` project

```
evals/                         # the project dir - launch every eval from here
  _env.py                      # once per repo: credentials + import path
  data/                        # one cache for every eval
  run_eval_<name>.py           # one per eval (or the whole probe, below)
  <name>/                      # one package per kept eval
    README.md  eval.py  agent.py  cases.csv  fixtures/  results/
```

Run from `evals/`: the cache and every relative path resolve against the working
directory, so a run from elsewhere builds a second, empty cache (`ev.cli` warns).
Credentials and production imports are solved ONCE in `_env.py` - load credentials
by absolute path, because a loader that resolves relative to the working directory
finds nothing from here. **They work in-process:** an eval calls production code
directly, so it is never "blocked on a dev server" or "needs keys Claude cannot
have" - check `_env.py` before concluding that.

## Start cheap: a probe that survives

A one-off question does not need a scaffold, but it does need to SURVIVE. A
gitignored `tmp/probe_*.py` answers the question once and is gone when the next
change to the same surface asks it again. Write the probe as one committed file,
`evals/run_eval_<name>.py`, and it is cached and re-runnable for the same effort:

```python
import _env  # noqa: F401 - credentials + import path, once per repo
import oryxflow.evals as ev
from pydantic import BaseModel
from myapp.reply import run_turn   # the LIVE function: run_turn(inputs, prompt_version)


class Turn(BaseModel):             # the inputs; every OTHER key becomes metadata,
    request: str                   # which is what `where='control'` filters on


CASES = [{'name': 'asks_for_edit', 'request': '...', 'control': False},
         {'name': 'control_question', 'request': '...', 'control': True}]

if __name__ == '__main__':
    r = ev.sweep(run_turn, cases=ev.load_cases(CASES, inputs=Turn), baseline='prod',
                 metric=ev.Metric('acted', 'acted'),
                 guardrail=ev.Metric('acted on control', 'acted', where='control',
                                     higher_is_better=False, budget=0.1),
                 prompt_version=['prod', 'preship'], repeats=3)
    r.verdict()
    r.report()                                 # results/<date>-<name>.md - commit it
```

**Never hand-roll `asyncio.gather`, and never write the probe in `tmp/`.** A
quick eval is the one you re-run MOST, so an uncached run re-bills every case on
every iteration, and a deleted one re-checks nothing next time. `ev.sweep` is
SHORTER than the asyncio it replaces.

Graduate it to a `<name>/` folder with `/oryxflow:eval-init` when the cases are
worth keeping in a file and the plan worth recording.

---

## The four questions

Every eval is these four answers; the code is bookkeeping. `/oryxflow:eval-plan`
asks them with proposals drawn from the repository and records them in
`evals/<name>/README.md`. Answer them BEFORE any scaffold exists - an eval
designed after its scaffold gets designed around the scaffold.

| # | Question | The rule that goes with it |
|---|---|---|
| 1 | **What is the function under test?** | The live entry point. Production code, NEVER a copy. |
| 2 | **What is the metric?** | The one number that answers "is it better", derived from the failure being chased. |
| 3 | **What must not get worse?** | The guardrail. Mandatory - see below. |
| 4 | **What is the baseline to beat?** | A git ref, materialized byte-exact. |

**Q1 - production code, never a copy.** A second copy of the instructions inside
`evals/` drifts from the shipping one within weeks, and then the eval measures the
copy. Import what ships.

**Q2 - derive the metric from the failure.** A SILENT failure (should have acted,
did not) -> *did it act*. A WRONG answer -> *is it right*, against an expected
column. A SLOW one -> latency as a budget. When the output is one of a fixed set
of labels, score it by comparison - an LLM judge on a closed label set buys
nothing but cost, variance and a second model's opinion on a string equality test.

**Never key a metric on labels the model writes itself.** A finding's rule name or
strength, authored by the model, drifts across runs, so a metric keyed on it
measures the model's naming, not its findings. Match on something the model cannot
rename - the quoted span, a planted cue, the expected label.

**Bars are references, not gates - and relative beats absolute.** Write down what
the baseline scores and where you would act, before the run. An absolute bar the
baseline itself cannot reach measures the model, not the change; observed bars
like ">= 9/12" were missed, then rewritten as "B >= A" after the fact. Prefer "no
worse than baseline on X" from the start, and expect to end in a judgement.

---

## The guardrail is mandatory

A change that improves "did the assistant act" by acting on EVERYTHING scores
100% and ships a regression. The metric alone cannot see that; only a control set
can. So every metric gets its opposite error, with a budget:

```python
metric    = ev.Metric('acted', 'did_act')
guardrail = ev.Metric('acted on a control', 'did_act', where='is_control',
                      higher_is_better=False, budget=0.10)
```

`column` is a BOOLEAN column averaged into a rate; `where` is a boolean column
name (or `~column` for its negation), NOT a query expression - so `is_control`
has to be a real column in `cases.csv`. Anything that is not a rate takes a
callable on the frame instead: `ev.Metric('mean latency', lambda d:
d['task_duration_s'].mean(), higher_is_better=False, budget=4.0)`.

Half of that is the declaration; the other half is the CASE SET. A guardrail over
zero control cases is a number, not a measurement - see "controls" below.

When the guardrail is over budget the answer is **"not a clean win"**, quoting the
guardrail number, however far the primary metric moved. Never an unqualified
"wins".

---

## Coverage before quality

**A quality rate is read AFTER a coverage metric, never alone.** A rate over a
filtered subset is gameable by shrinking the subset: "quality of the turns where
it said something" goes UP when it says something less often.

In an observed eval, one prompt scored respectably on output *quality* largely by
staying silent on a third of the turns. Quality moving 31% -> 100% only meant
something because yield moved 1.62 -> 2.42 in the same direction. Had yield fallen,
the quality number was the regression, not the win.

Declare the pair so the runner prints coverage FIRST:

```python
metric = ev.Metric('quality', 'is_good', where='wrote',
                   coverage=ev.Metric('yield', lambda d: d['n_written'].mean()))
```

If coverage fell while quality rose, **that is the headline** - lead with it.

---

## The case set

### Cases must be genuine

Read each case's own fixture and ask: **would a correct model actually have to act
here?** A fixture that names a state must actually BE in that state. One harness scored correct refusals as FAILURES because its fixture asked
for a change that had already been made - the model was right and the eval was
wrong, and it made a good prompt look broken. Either alter the fixture so the work
is genuinely outstanding, or reclassify the row as a control and score it that way
on purpose.

### Real and synthetic never blend

A synthetic set written by the same mind that wrote the prompt FLATTERS it. Tag
every row (`synthetic=0` harvested, `synthetic=1` invented), make the headline
**real-only**, and report the synthetic result beside it. A blended rate hides
exactly how much of the score is self-graded.

Harvest real cases before inventing any: failure reports, tickets, test fixtures,
recorded transcripts, quotes in requirements docs, production exports. Then say
plainly what you could NOT find - and ASK for a real export rather than
substituting invention for it. `/oryxflow:eval-cases` runs that harvest.

### Holdout: any case quoted in the prompt

Grep the prompt and its templates for each case's literal wording. **A case whose
text is embedded in the prompt is held out of EVERY arm**, or the comparison is
scored against its own answer key and the arm containing the example wins for
free. Tag it `holdout=1` and keep the row - deleting it loses the record that it
was considered.

### Three categories a set is silently weaker without

- **Controls** - the correct behavior is to DO NOTHING. Without them "act always"
  scores perfectly, and "act more" is the easiest accidental change to make.
  Roughly a quarter of the set. These are what turn the guardrail into a real
  number.
- **The needs-user-input trap** - a request the assistant genuinely cannot fulfil
  without something only the user has. The correct behavior is usually to ASK
  while still doing whatever useful work is available, so this case distinguishes
  "handled it properly" from "punted". No other case can see that.
- **The mood pair** - the same semantic request as an imperative and as a
  question. Phrasing alone flips behavior more often than anyone expects, and a
  uniformly imperative set cannot see it. The two rows share every other axis
  value, so the difference has exactly one explanation.

### Design AXES, not a case list

A flat list of failures distinguishes nothing. Crossing a phrasing axis against a
state axis is what separates a WORDING problem from a CONTEXT problem. Every axis
must become a real COLUMN in `cases.csv` - unrecognized columns become case
metadata, which becomes a DataFrame column, which is a report slice. An axis that
lives only in your head produces no breakdown and the design was for nothing.
2 x 3 x 3 pruned lands in the 15-25 band without padding.

---

## The baseline: a git ref, not a string patch

**Check the baseline out of git.** `ev.git_tree(ref, paths)` materializes the
files as they were, byte-exact, and stamp the arm with `ev.git_sha(ref)` so the
resolved sha lands in the cache key rather than a moving ref name.

```python
baseline_dir = ev.git_tree('HEAD~1', ['prompts/', 'templates/reply.md'])
```

Why not reconstruct it by replacing strings in the live files: **a replacement
cannot put back a section the change DELETED.** A real harness found this the hard
way - two of its four template changes were deletions, and the string-replacement
baseline quietly reconstructed nothing while reporting a clean run. It also decays
silently as the live template moves and the anchors stop matching.

`ev.Variant(old, new)` is the right tool for a **probe** - a rewrite not yet
shipped, which has no ref to check out. It MUST raise when its anchor is gone; a
probe that silently no-ops is a baseline bug wearing a different hat. Probe, yes;
baseline, no.

---

## Reuse before you write

pydantic-evals ships most of what a case needs scored. Check here first:

| you need | use |
|---|---|
| one yes/no judgement of fuzzy quality | `LLMJudge(rubric=, model=, include_input=)` |
| a scored rubric with explicit steps | `GEval(criteria=, evaluation_steps=)` |
| exact match on the expected answer | `EqualsExpected()`; `Equals`, `Contains`, `IsInstance` |
| right tools, right arguments, right order | `ToolCorrectness`, `ArgumentCorrectness`, `TrajectoryMatch`, `HasMatchingSpan` |
| a budget on tool calls / model requests | `MaxToolCalls`, `MaxModelRequests` |
| a confusion matrix / precision-recall over a label | `ConfusionMatrixEvaluator`, `PrecisionRecallEvaluator` in `report_evaluators` |
| per-case setup: stub a search API, seed a record | `CaseLifecycle` |

Patterns that need no new API: a **model** is just another arm parameter (pinned to
a snapshot, folded into `code_version()`); a **conversation** is one case whose
`case()` replays every turn on the state the previous one returned and returns
per-turn columns; **"zero false negatives"** on a flag is a confusion matrix over
`expected`, read per class.

Trace-reading evaluators (the tool-call ones, `HasMatchingSpan`) score while the
run's trace exists, and only then. To keep a tool-call check re-scorable for free,
have `case()` return the calls it made and score those.

---

## Judge rules (when the metric needs an LLM)

Three rules, all cheap to follow:

1. **A different model family from the model under test.** Self-preference is
   real and avoiding it costs nothing.
2. **Grade the RAW output**, not the post-sanitizer output. Grading what the
   backstop cleaned up measures the backstop, not the prompt.
3. **Every field of the judge's output schema is REQUIRED.** An optional flag is
   one the model can decline to fill, and an unfilled flag reads downstream as a
   pass. There is no such thing as an optional judge field.

And do not reach for a judge at all when the output is one of a fixed set of
labels - compare the strings.

---

## Nothing between the model's output and the scorer

Any truncation, normalization or clean-up applied before scoring means you are
measuring that transformation, not the prompt.

The observed instance: a harness capped its output field at 2000 characters for
CSV readability, and its metric read the LAST LINE of that field - so it sliced
long replies mid-sentence and scored the model down for the harness's own
scissors. Every arm scored 0%.

`result.df` renders long text twice - `<field>` full and `<field>_preview`
capped. **Score and diagnose from the full column, always.** The preview exists
for eyeballing a frame, and reading it in a metric reproduces exactly this bug.

---

## Distrust the instrument before you interpret it

**A perfect score is not a result.** A single arm at 100% means the case set has
stopped discriminating - it can no longer show a regression OR an improvement. The
library flags it. The response is harder cases, not a victory lap; a suite that
never fails is one nobody can learn from. (Practitioner rule of thumb: a ~70% pass
rate is a more useful eval than a 100% one.)

**A metric identically 0% or 100% in EVERY arm is measuring the harness.** 0%
before and 0% after is almost never a model result. The library flags it (the
dead-metric line, plus a denominator-drift line when the population moves). When
either fires:

1. Investigate it FIRST. Do not narrate a result sitting on top of an unexplained
   flag - a clean story told over a broken metric is worse than no answer, because
   it gets believed.
2. Read ONE FULL raw output for a case the metric scored as failing and confirm
   with your own eyes that the metric reads what you think it reads.
3. Report it as an EVAL BUG, fix the harness, re-run. No model verdict comes out
   of that run.

This heuristic is what caught the truncation bug above - it presented as a
plausible model failure and was an artifact, spotted only because a human noticed
the two zeros. Even with no flag raised, spot-check one failing row per arm before
diagnosing anything.

A second instrument failure worth naming: an all-error sweep that CACHES. If
credentials are missing or the harness ran from the wrong directory, every case
raises, the sweep completes, and an empty result caches as if it were a
measurement. An empty or all-error frame is a FAILURE, never a pass - and re-run
with `--reset` after fixing, or that empty cell is served forever.

A third instrument failure, and the quietest: **a metric only some rows carry a
verdict for.** An LLM judge that grades one surface and skips another, or that
was switched off for a cheap run, leaves the metric column null on the rest. The
library now drops those rows from the rate and says how many it dropped -

```
  8 of 16 eligible rows carry no pairing verdict and are OUT of the rate
```

- so read that line before the number above it. The rate is over the rows that
were judged, which may be a small and unrepresentative slice of the run. When
NOTHING was judged you get `NOT MEASURED` and `n/a`, never `0%`; if you see it,
whatever fills that column did not run, and there is no model result here at all.

---

## Reading the verdict

Never state a verdict more confidently than the library did. Its hedging is a
floor, not a suggestion.

With a baseline arm (`baseline=`, or an arm named `baseline`) the verdict reports
every arm's difference from it and names NO winner - on purpose. Real results are
mixed, and the useful output is a written judgement: what moved against the plan's
bar, what is inside noise, the trade-off, and what you would do and why.

| What the block shows | What you say |
|---|---|
| Delta INSIDE the interval | *"inside noise at N reps; raise repeats before calling this real"* - no winner is named |
| Guardrail over budget | *"not a clean win"*, quoting the guardrail number |
| Coverage fell, quality rose | Lead with coverage - the quality gain is the artifact |
| Wide interval / few reps / high error count | First paragraph, not a footnote |

"Inside noise" is a complete answer. It is not "trending better", not
"directionally positive", not "slightly ahead". **Raise `repeats`** when the delta
matters and sits inside the interval - the cost is linear in the reps, so quote it
(`repeats=3 -> 5` is 2 more calls per case per arm) and let the user decide. Raise
reps also when the task is high-variance (long free-form generation, temperature
above zero); a deterministic classification barely needs more than one.

Read the outputs, not only the rate: `r.side_by_side()` (or `--side-by-side`)
writes every arm's output for the cases where the arms disagree, from the stored
outputs, with no model calls. A scorer that rewards the wrong thing survives every
rate and dies on the first read.

Then do the part no library can do: **diagnose**. Group the failing rows by
MECHANISM, not one by one - "the imperative phrasings pass and the interrogative
ones do not" is a finding, "5 cases failed" is not. Quote one short verbatim
excerpt per mechanism from the full output column. Close on the residual weakness
in the WINNING arm, not on the headline. And report a mixed result straight: a
targeted fix that improved two labels and regressed a third is a MIXED RESULT, in
those words - do not lead with the improvement and bury the regression, and do not
average them into one cheerful number.

---

## API surface

```python
import oryxflow.evals as ev
```

| Call | What it does |
|---|---|
| `ev.sweep(fn, *, cases=, metric=, guardrail=, slices=, repeats=, watch=, evaluators=, baseline=, reset=, rescore=, cost_per_call=, **arms)` | Run the cross product; returns `EvalResult`. Each keyword in `**arms` is an axis (`prompt_version=['prod', 'preship']`); a single-valued one is a fixed setting and stays out of the arm name. `baseline=` names the arm the others are reported against. `reset` re-calls the model; `rescore` re-runs only the scorers. |
| `watch=` | Glob patterns (or a callable) for files the target READS - prompts, `.sql`, config, and the module holding your agent code. Without it they are outside the cache key, so editing a prompt re-runs NOTHING and you read last week's numbers. A pattern matching no file raises. **The single most important argument for cache correctness.** |
| `evaluators=` | pydantic-evals evaluators for the generated dataset - how a case is scored against its `expected` column. The target sees only `inputs`, so a classifier eval needs this. |
| `ev.Metric(label, column, where=None, higher_is_better=True, budget=None, coverage=None)` | One number. `column` = a BOOLEAN column averaged into a rate, or a callable on the frame. `where` = a boolean column name (`~col` negates), not a query. `budget=` makes it a guardrail; `coverage=` prints first. Rows carrying an `error` are dropped from every rate - a case that raised is not evidence either way - and so are rows whose metric column is NULL: unmeasured is not failed. |
| `ev.load_cases(path, inputs=..., expected=..., name_col='name')` | CSV/YAML/JSONL -> cases. Columns route by name: `inputs` fields validated by pydantic, `expected*`, everything else becomes metadata (= a report slice). `@fixtures/x.md` substitutes that file's text. Reserved: `synthetic`, `holdout`, `expect_*`, and **`arm`** - that is the sweep's own label for a cell, so a metadata column of that name is refused up front. Name yours `surface` / `variant` / `write_arm`. |
| `ev.judge_alignment(df, judge, human)` / `ev.corrected_rate(observed, alignment)` | TPR / TNR / Cohen's kappa of a judge against human labels, and the Rogan-Gladen correction of a rate for a known-imperfect judge. Refuses to correct when TPR+TNR <= 1. |
| `ev.git_tree(ref, paths)` / `ev.git_sha(ref)` | Materialize a baseline byte-exact / resolve the ref to a sha for the cache key. |
| `ev.PromptArm(ref=/globs=, paths=, root=, subdir=)` | Where one arm READS its prompts and the cache key that MATCHES, in one object - `.dir()` and `.code_version()`. Written by hand they are two places, and an arm reading a checked-out tree while keyed on live files is a silent staleness bug. |
| `LLMJudge(rubric=, model=, include_input=)` (pydantic-evals) | The judge for ONE yes/no question. Do not hand-write an Evaluator for that - this is a library, use it. Write your own only for several fields per case, or a verdict per item inside the output. |
| `ev.Variant(old, new)` | Anchored replacement for an unshipped PROBE. Raises when the anchor is gone. |
| `ev.TaskEval` | The keepable form: override `async def case(self, inputs)`; declare `metric` / `guardrail` / `slices` / `code_version()` / optional `baseline`. Class names must be unique across `evals/` (one shared cache). |
| `ev.cli(Task)` | `run_eval_<name>.py` in three lines - gives `--check` (preflight only: ONE real call, no bill, no sweep), `--repeats`, `--concurrency`, `--reset`, `--rescore`, `--side-by-side`, `--csv`, `--yes`. The cost confirmation offers the same probe inline as `c`, so a first run does not have to know the flag exists. |

`EvalResult`: `.df` (per-case frame - one row per case x arm), `.verdict()`,
`.report(path)`, `.side_by_side(path=None, all=False)`, `.best()` ->
`(arm, value, interval, clean)`.

**The frame already holds more than people reach for.** Before computing anything,
check for a column: your output fields; `expected` / `expected_*` (the case's
expected output - so a confusion matrix is a crosstab of two columns, NOT a join
back on case name); one column per evaluator (assertions, scores, labels, by
evaluator name); every metadata column from the case file; `task_duration_s` /
`total_duration_s`; `error` and `evaluator_errors`; and anything the task recorded
with `increment_eval_metric` (token counts - the verdict then prints
`measured usage: input tokens ...`, which is the real number rather than the
pre-run estimate).

**Write `case()` and any LLM judge `async`.** oryxflow's own engine is entirely
synchronous - this is not its requirement - but `concurrency` is scheduled as
coroutines by the eval runner, so a blocking `def` holds the loop and the cases
run ONE AT A TIME while the knob still reads as set. Same numbers, 5x the wall
clock (8 half-second cases at concurrency=8: 1.0s async, 4.9s sync). The library
warns when it sees this; there is no other sign.

**A judge nobody checked is an opinion with an interval printed round it.**
Before quoting anything a judge produced at scale: hand-label a sample of cases
(aim for ~100; below ~50 the rates are too noisy to act on), put the labels in a
column, and name it - `ev.Metric('pairing', 'pairing_holds', human='pairing_human')`.
The verdict then reports TPR / TNR / Cohen's kappa and a corrected rate.

**Read kappa, not agreement.** Raw agreement inflates under class imbalance: on a
90%-pass set, a judge that says pass to everything scores 90% agreement and has
learned nothing. Kappa nets out chance, so that judge scores 0 - and the library
refuses to correct anything with it.

**An unvalidated judge does not just add noise, it SHRINKS your effect.** An
imperfect judge pulls every rate toward its own error floor, so a real 85% vs 55%
reads as 78% vs 60% through a judge that is 88% accurate. If a delta lands "inside
noise" and the metric is judge-scored, validating the judge is a better move than
raising repeats.

**Do not write a judge you do not need.** `LLMJudge(rubric=..., model=...)` from
pydantic-evals covers a single yes/no question about the output and lands as a
column your metric reads - a complete two-arm eval with a judge, intervals and
caching is ~20 lines. Write a custom `Evaluator` only when one verdict per case
is genuinely not enough (several fields, or one verdict per item in the output);
then return a dict, and `{}` when there is nothing to judge.

**Put an LLM judge in an `Evaluator`, not in `case()`.** Scoring is the
evaluator's job: a judge failure is then a scoring failure rather than a lost
case, and returning a dict gives each verdict field its own frame column instead
of being flattened into the output model by hand. Return `{}` when there is
nothing to judge - those rows are NOT MEASURED, which the metric excludes rather
than counts as failures.

**Let `case()` raise.** Catching the exception and returning an error field makes
the runner record a SUCCESSFUL case and leaves the failure list empty - the eval
then reports a rate computed over cases that never ran. Errors are data; swallow
them and the harness lies twice (a wrong rate, and a clean bill of health).

Seams for a replacement runner: override `_evaluate()` and `_to_frame()` on
`TaskEval`; everything downstream reads only the frame.

**Each cell is cached in two stages: the model calls, then the scoring.**
`code_version()` on a `TaskEval` names what the ARM reads - prompt files, a git
ref, a model id - and keys only the model-call stage, together with the code
`case()` runs and the case set. The scorers key the scoring stage on their own
(`scorer_version()`, default: every evaluator's code and configuration), so
editing a scorer or a judge rubric re-scores the stored outputs with NO model
calls - the bill says `re-scoring N arms from stored outputs`. The function
form's equivalent of `code_version()` is `watch=`: files the target READS (it
already follows the code the target calls). A missed file is not silent - a
`StalenessWarning` says the cached output is being reused - but it is not a
re-run.

---

## The commands, in order

All four are MANUAL (`disable-model-invocation: true`) - two write files and one
spends money. Suggest them by name; never invoke one.

1. `/oryxflow:eval-plan` - settle the questions, write `evals/<name>/README.md`,
   write no code.
2. `/oryxflow:eval-init` - scaffold from the template (`_env.py` once per repo),
   fill it from the plan, end in a 3-call smoke run.
3. `/oryxflow:eval-cases` - harvest real cases, propose axes, grow the set to 15-25.
4. `/oryxflow:eval-run` - print the bill, run, check the harness, read the
   side-by-side, write a judgement to `results/<date>-<arms>.md`.

Skipping straight to `eval-init` is the common mistake: an eval whose metric was
never argued measures whatever the scaffold happened to declare.

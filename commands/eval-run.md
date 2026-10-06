---
description: Run an oryxflow eval and interpret the result - resolve the arms, print the projected bill (cases x arms x reps, cached/new split, cost, duration) and wait for confirmation, run the sweep from evals/, check the harness for a dead metric before believing any number, read the outputs side by side, then write a judgement - not a pass/fail - to results/<date>-<arms>.md. Bills the user - only ever run when asked.
disable-model-invocation: true
---

# Run an eval and interpret the result

Run the eval in `${CLAUDE_PROJECT_DIR}` and turn its output into a defensible
answer to "is the change better?".

This command SPENDS THE USER'S MONEY on API calls. Never start a run without
showing the bill and getting a yes (see step 2). The library does the arithmetic
- the rates, the intervals, the paired delta, the guardrail marks. Your job is
the part it cannot do: verify the instrument, then diagnose the failures. Do NOT
restate what the verdict block already prints - interpret it.

`$ARGUMENTS` is the arm selection (e.g. `prod vs preship`), optionally with
`--yes` to skip the confirmation. Both are optional; see steps 1 and 7.

## 1. Resolve the arms

- Read `evals/<name>/README.md` (written by `/oryxflow:eval-plan`) - it names the
  metric, the guardrail and the baseline ref. If there is no eval directory, STOP
  and point the user at `/oryxflow:eval-init`.
- If `$ARGUMENTS` names arms (`prod vs preship`), use them.
- If it does not, use the plan's baseline as one arm and the live code as the
  other. Say which two you picked and why, in one line, before the bill.
- Every run launches FROM `evals/` (`cd evals`): the shared cache and `_env.py`
  live there. A run from anywhere else warns and builds a second cache.
- If the user named an arm the eval does not declare, STOP and list the arms that
  exist. Do not silently substitute a neighbour.

## 2. Print the bill and WAIT

Before any call is made, print:

- `<Task> | <C> cases x <A> arms x <R> reps = <N> calls`
- the cached / new split: `cached <k> | new <m>`
- the estimated cost of the NEW cells, and the estimated wall-clock duration at
  the configured concurrency
- **why each new cell is new.** There are only two reasons and the user needs to
  know which: the arm has never been run, or a prompt/template it depends on
  changed since it last ran (oryxflow's computed code version invalidated it).
  Name the changed file.

Get the numbers from the library, not from a guess: the bill is printed by the
run itself, before anything is billed.

Then WAIT for confirmation whenever there is at least one uncached cell. A run
that is entirely cached costs nothing - go straight to step 3 and say it was
free. `--yes` in `$ARGUMENTS` skips the wait; nothing else does.

The confirmation offers a one-call probe: `(y/n/c=check one call first)`. Answer
`c` when the eval has never run, or when anything about its wiring changed - it
spends ONE call, says whether the harness works, and asks again. That is one
billed call, not zero; say so if you propose it.

## 3. Run, print the verdict, record it

Run the sweep from `evals/` - `python run_eval_<name>.py` with the arm /
`--repeats` / `--concurrency` flags, or `ev.sweep(...)` directly. Print the
verdict block the library produces, verbatim. It already contains, and you must
not paraphrase or recompute:

- the per-arm rate with `n` and a 95% confidence interval
- the paired delta with its interval and an `outside noise` / `inside noise`
  reading
- the guardrail section with `over budget` marks
- the coverage metric, rendered first when one is declared
- `synthetic n=K` beside a real-only headline, plus the holdout-excluded and
  failure counts
- the dead-metric line and the denominator-drift line when they fire
- the unmeasured line when some rows carry no verdict (`N of M eligible rows
  carry no <metric> verdict`), or `NOT MEASURED` when none do. Treat either the
  way you treat a dead-metric flag: the rate above it is over a subset, and
  `NOT MEASURED` means whatever fills that column never ran - there is no model
  result in that block to report
- a caveat line when an interval came from a Wilson fallback instead of the
  bootstrap

The shape:

```
ReplyEval | 22 cases x 2 arms x 3 reps = 132 calls
  cached 66 | new 66

YIELD (higher is better)
  baseline   64%  (42/66)   95% CI [51%, 75%]
  live       91%  (60/66)   95% CI [82%, 96%]
  D  live - baseline  = +27pp  [+15pp, +39pp]   outside noise

VERDICT  live vs baseline on yield: +27pp [+15pp, +39pp], outside noise.
```

With a baseline arm the verdict reports every arm AGAINST it and names no
winner, on purpose: that is your job, in step 5.

Add `--side-by-side` to the run (or re-run the same command with it - every cell is
cached, so that costs nothing). It writes every arm's output for the cases where
the arms disagree, plus failures, to
`evals/<name>/results/<date>-<arms>-side-by-side.md`.

Write the run up to `evals/<name>/results/<date>-<arms>.md`: the verdict block,
the harness check from step 4, the judgement from step 5, and the proposed next
arm. Print both paths. Both files get committed - small, and paid for.

## 4. CHECK THE HARNESS BEFORE YOU BELIEVE THE NUMBERS

Do this BEFORE step 5, every run, and say in the report that you did it.

**A metric that is identically 0% or 100% in every arm is almost never a model
result - it is measuring the harness.** The library flags this above the tables
(the dead-metric line), and flags a moving denominator on its own line. When
either fires:

1. Investigate it FIRST and say so plainly. Do NOT narrate a result that sits on
   top of an unexplained flag - a clean-looking story told over a broken metric
   is worse than no answer, because it gets believed.
2. Read ONE FULL raw output for a case the metric scored as failing, and confirm
   with your own eyes that the metric reads what you think it reads. Use the full
   `<field>` column, never `<field>_preview` (see step 5) - reading the preview
   here would reproduce the exact bug this step exists to catch.
3. Report the finding as an eval bug, fix the harness, and re-run. Do not report
   a model verdict from that run.

The observed instance: a real harness capped its output field at 2000 characters
for CSV readability, and its metric read the last line of that field - so it
sliced long replies mid-sentence and scored the model down for the harness's own
scissors. Every arm scored 0%. It presented as a plausible model failure and it
was an eval artifact, caught only because a human noticed the two zeros.

The general rule behind it: **nothing may sit between the model's output and the
scorer.** Any truncation, normalization or clean-up applied before scoring means
you are measuring that transformation, not the prompt.

Even with no flag raised, spot-check one failing row per arm before diagnosing -
the side-by-side file is the fastest way to read them.

## 5. Diagnose and judge - the part no library can do

A verdict without a mechanism is not actionable, and the library deliberately
names no winner. Read the per-case frame and the side-by-side file, explain WHY,
and end in a judgement a person can act on.

`result.df` is the escape hatch: one row per case x arm, with `case_name`, `arm`,
one column per metadata key (so per-slice breakdowns work), one per assertion or
score, `task_duration_s`, `error`, and the flattened output fields. **Long text
fields appear twice - `<field>` full and `<field>_preview` capped. Diagnose from
the full column, always.**

Produce:

- **The failing rows grouped by mechanism**, not listed one by one. Group by the
  metadata slices that exist (label, phrasing, state) and name the pattern.
- **The mechanism, named.** "The imperative phrasings pass and the interrogative
  ones do not" is a finding. "5 cases failed" is not.
- **Quoted evidence.** One short verbatim excerpt per mechanism, from the full
  output column. Quote, do not summarize.
- **Residual weakness in the WINNING arm.** Close on what is still wrong with the
  arm you are recommending, not on the headline number.
- **The next arm, with its cost.** Name the concrete change to try and what the
  run would bill (`N new cells, about $X`). Suggest it; do not run it.

**Report a mixed result straight.** A targeted fix that improved two labels and
regressed a third is a MIXED RESULT, not a win - say so in those words. Do not
lead with the improvement and bury the regression, and do not average them into
one cheerful number.

**Close with the judgement, in four short parts:** what moved (and against which
reference in the plan's bar), what is inside noise, the trade-off if there is one,
and what you would do - ship, iterate on a named arm, or gather cases - with the
reason. The plan's bar is a reference point for that judgement, not a gate.

## 6. Never state a verdict more confidently than the library did

The verdict block's own hedging is a floor, not a suggestion.

- Delta INSIDE the interval -> *"inside noise at N reps; raise repeats before
  calling this real"*. Not a winner. Not "trending better". Not "directionally
  positive".
- Guardrail over budget -> *"not a clean win"*, quoting the guardrail number,
  even when the primary metric moved a lot. Never an unqualified "wins".
- A quality rate is read AFTER its coverage metric. A rate over a filtered subset
  is gameable by shrinking the subset - quality can climb because the model
  answered less often. If coverage fell while quality rose, that is the headline.
- Real cases are the headline. Report `synthetic n=K` beside it, never blended
  in.
- A wide interval, few reps, or a high failure / error count is a caveat that
  belongs in the first paragraph of the report, not a footnote.

## 7. No arguments, existing eval - report what is stale

With no `$ARGUMENTS` in a directory that already has results:

1. Compare the current code version of each arm against the last recorded run.
2. Report what changed since then and which arms are therefore stale, naming the
   file that changed for each.
3. Offer to re-run ONLY the stale arms, with that reduced bill. The fresh arms
   are cache reads and cost nothing - comparison across time is a cache read, not
   a new run.

## Reference

- API: `import oryxflow.evals as ev`. `ev.sweep(...)` returns an `EvalResult` with
  `.df` (the per-case frame), `.verdict()`, `.report(path=None)`,
  `.side_by_side(path=None, all=False)`, `.best()`. Docs:
  https://docs.oryxflow.dev/llms.txt - read them before the source.
- CLI (`run_eval_<name>.py`, run from `evals/`): `--check` (preflight ONLY - one
  real call, no bill, no sweep), `--repeats`, `--concurrency`, `--reset` (drops
  BOTH stages, so it re-bills the model calls - confirm first), `--rescore`
  (re-runs only the scorers over stored outputs: no model calls, but an LLM judge
  still bills per case), `--side-by-side`, `--csv`, `--yes`. The cost confirmation also offers that
  same probe inline as `c`.
- A scorer or judge-rubric edit costs no model calls: the bill shows
  `re-scoring N arms from stored outputs`. Say so when proposing one.
- Raise `--repeats` before believing a small delta; that is the answer to "inside
  noise", and its cost is linear in the reps - quote it when you propose it.

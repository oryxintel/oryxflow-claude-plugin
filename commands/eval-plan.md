---
description: Decide what an LLM eval actually measures, before any code exists - gather the change and its call path from the repo, then settle six questions (goal, models, prompts, measure, guardrail, data) with a proposal drawn from what is really there. Writes only evals/<name>/README.md, the durable record of what is measured and why. Run it when you changed a prompt and cannot tell whether it is better.
disable-model-invocation: true
---

# Plan an eval: decide what is measured, write no code

This is the DECIDE step. It settles six questions and records the answers in
`evals/<name>/README.md`. It writes NOTHING else - no `eval.py`, no `cases.csv`,
no scaffold. `/oryxflow:eval-init` does the generating, and it reads this file.

Why the split: an eval that is designed after its scaffold exists gets designed
around the scaffold. The six answers below are the whole eval; the code is
bookkeeping. Target directory: `${CLAUDE_PROJECT_DIR}`.

`$ARGUMENTS` (optional) is the eval name, and/or a hint at what changed. With no
argument, name the eval after the surface under test (`evals/reply_tone/`), and
confirm the name with the six proposals. The name becomes a Python package:
lowercase, underscores, no dashes.

## 1. Gather the context first - shell and read, never guesswork

Every proposal in step 2 must come from something you actually read. If you
cannot find it, say so and ASK; do not invent a plausible answer.

- **The change.** `git diff` and `git diff --staged` in the working tree, plus
  `git log --oneline -20 -- <prompt/template paths>`. You need the exact commit
  the change sits on top of - that is the baseline in question 4.
- **The call path.** From the changed file to its entry point: who reads the
  template, what function wraps it, what the caller passes in. Grep for the
  template filename, then follow the callers up. Read the entry point.
- **The failure being chased.** Search the repo for a failure report, ticket,
  bug note, TODO or test that describes what went wrong. That text decides the
  metric in question 2, so quote it rather than paraphrasing.
- **Existing evals.** Does `evals/` exist? If `evals/<name>/README.md` already
  exists, STOP and report it - offer to revise it, and change nothing until the
  user answers. An existing eval on the SAME surface is usually better extended
  (a new arm, more cases) than duplicated - say so if you find one. If
  `evals/_env.py` exists, read it: it already answers how this repo's evals
  import production code and load credentials (Q6).
- **The libraries' docs, before their source.** Read
  https://docs.oryxflow.dev/llms.txt (the LLM evals pages) and
  https://pydantic.dev/docs/ai/evals/ before proposing any API. pydantic-evals
  already ships judges, tool-call checks and confusion matrices - propose those
  rather than hand-written ones. The installed version wins over the docs.

Report what you found and, plainly, what you could not find.

## 1b. Look at real outputs before naming a metric

A filed ticket tells you the failure somebody NOTICED. It does not tell you the
failure distribution, and a metric derived from one report measures one report.
The most reliable way to pick a metric is to read outputs until the failure modes
stop being new:

1. **Get 20-50 real outputs.** Logs, a fixture set, a scratch script that runs the
   entry point over realistic inputs - whatever exists. Say which it was.
2. **Open-code them.** One short note per output about what is wrong with it, in
   your own words. Do not classify yet; do not consult a metric.
3. **Axial-code the notes.** Group them into a handful of named failure modes and
   COUNT each one. That count is the argument for the metric.
4. **Stop at saturation.** When ~20 more outputs add no new category, stop.

Report the taxonomy with counts, most frequent first, and quote one real example
per mode. The metric in Q2 should then be the top mode, or say explicitly why not.

**If no real outputs are available, say so in one line and continue** - the plan
records that the metric rests on a single report rather than on a counted
distribution. That is a known gap, not a blocker, and it belongs in `Known gaps`.

Do not skip to step 2 because the ticket looks clear. The common outcome of this
step is that the reported failure turns out to be the third most frequent one.

## 2. The six questions

Ask ALL SIX in one message. The questions are fixed; the proposals are whatever
is actually in the repository. Give each answer a PROPOSAL and a one-line WHY,
then wait. Accept `yes` / a correction per question / `adjust`.

They are the six sections the plan file has, in its order - goal, models,
prompts, measure, guardrail, data - so the answers drop straight into it.

### Q1. What is the goal - what decision does this number inform?

Propose it from step 1, in four short parts. This is the section everything else
is downstream of, and an eval written straight from a ticket measures the ticket.

- **The decision.** Who acts on the result, and what they do differently at a good
  number versus a bad one. If nothing changes either way, say so - that is a
  spot-check, not an eval, and it is worth telling the user before they pay for a
  matrix.
- **Business background.** What the surface does, who uses it, and what a bad
  output costs. That cost is what decides how much noise is tolerable in Q4.
- **What ships today**, and the base prompt it comes from, by path.
- **The failure being chased**, QUOTED from the report you found in step 1, plus
  the counted taxonomy from step 1b if you have one.

Close with one honest line: is this the frequent failure, or the noticed one?

### Q2. Which models - the one under test, and the one judging?

Name BOTH by import path and model id, from what the repository actually uses.
Never by family alone: "two different families" is not runnable.

- **Under test: whatever production runs.** Evaluating a bigger model than the one
  that ships answers a different question. If production is pinned to a cheap
  model for cost or latency, the eval is pinned to it too - or model choice
  becomes a second arm, said out loud.
- **Judging: a DIFFERENT family from the model under test.** Self-preference is
  real and avoiding it is free.
- **Ask whether a judge is needed at all.** A closed label set is scored by
  comparison; a judge there buys cost, variance and a second opinion on a string
  equality test.
- **Both ids pinned to a snapshot**, and folded into the arm's `code_version()`
  so a model change invalidates the cell instead of being served from it. An id
  that silently moves makes two runs incomparable while looking identical.

Say plainly that this is the cheapest answer to get wrong now and the most
expensive to discover after a full matrix, and ask whoever owns the prompt to
push back on it specifically. Record a disagreement you overruled, and why, under
`Judgement calls`.

### Q3. What are the prompts - current, proposed, and the function under test?

Propose the live entry point you traced in step 1, by import path
(`app.reply:draft_reply`), the template it reads, and what each arm reads.

State the rule, and its DIRECTION: **the baseline arm always reads production,
never a copy.** A copy of the shipping instructions kept inside the eval
directory drifts from the real one within weeks, and then the eval measures the
copy. The reverse is fine and is the whole point - a candidate developed in the
eval and promoted after it wins.

**The baseline arm is a git ref, checked out.** Propose the commit before the
change, from step 1, materialized with `ev.git_tree(ref, paths)` and stamped with
`ev.git_sha(ref)`.

Say why in one line: a string replacement cannot restore a section the change
DELETED, and it decays silently when the live template moves. A real harness
found this the hard way - two of its four template changes were deletions, and
the replacement baseline quietly reconstructed nothing. Do not offer a
string-patch variant as the baseline.

`ev.Variant(old, new)` is still right for a PROBE - a rewrite not yet shipped,
which has no ref and must raise when its anchor is gone. Mention it only if the
user is evaluating an unshipped rewrite as a third arm.

**If the prompt is a Python string constant, say so and propose extracting it.**
Check this before proposing anything else here - grep the entry point for a
triple-quoted constant, an f-string, or instructions assembled inline. A prompt
that lives inside `app/reply.py` breaks three things at once: `code_version()`
has no file to hash, `ev.git_tree` has no directory to check out as a baseline,
and nobody can read the prompt without importing the application.

Propose the extraction as part of this eval's work - move the string into
`prompts/<name>.md` (YAML front matter for the metadata, markdown body for the
prompt), load it at import, and confirm the rendered text is byte-identical
before and after. Then the arms key on `prompts/*.md`.

If the user does not want the extraction now, that is fine - the arm hashes the
MODULE instead (`oryxflow.hash_files('app/reply.py')`). Say plainly what that
costs: every unrelated edit to that file re-runs the arm, and there is still no
baseline arm, because there is no prompt directory for git to hand back. Put it
in `Known gaps`.

**Say which side of the line each arm's prompt starts on.** The baseline reads
production. A candidate that has not shipped anywhere may live in the eval
directory until it wins. Both are legitimate; a copy of a SHIPPING prompt inside
the eval is not.

**If any arm's prompt lives in the eval, record the promotion step under
`Judgement calls` now**, while someone is thinking about it - after a win nobody
comes back to this file. The sequence: copy the winning file into production
byte-exact, repoint that arm at production, re-run that one cell, confirm the
number reproduces. That re-run is what proves the prompt that shipped is the
prompt that won; reformatting on the way in is the failure it catches, and it is
otherwise invisible.

A prompt that BUILDS or harvests cases is eval-owned forever and is never
promoted. Note it as such if the plan has one.

Present the arms as a table - arm, what it reads, what it is cached on - because
those three drifting apart is the failure this question exists to prevent.

### Q4. What is the measure - the metric, the bar, and the difference to detect?

Derive it from the failure in step 1, do not pick a generic one:

- a SILENT failure (it should have acted and did not) -> *did it act*
- a WRONG answer -> *is it right*, against an expected column
- a SLOW one -> latency, as a budget

Warn when the output is one of a fixed set of labels: score it by comparison,
not with an LLM judge. A judge on a closed label set adds cost, variance and a
second model's opinion to a string equality test.

**Prefer BINARY over a 1-5 scale.** Adjacent points on a scale have no consistent
meaning between raters or between runs, and detecting a difference needs a much
larger sample. If gradations matter, decompose into several binary checks rather
than one scale.

**If the metric is judge-scored, plan how the judge gets validated.** Name the
column the human labels will live in and roughly how many cases get labelled
(~100 is the working target; below ~50 the rates are too noisy to act on), and
propose `ev.Metric(..., human='<column>')`. An unvalidated judge does not merely
add noise - it pulls every rate toward its own error floor and SHRINKS the
difference you are trying to measure. Record it under `Judgement calls`.

**Name the UNIT the number is computed over, and how it reaches the table.**
The eval produces one row per case, per arm, per repeat, and every number the
verdict prints is a column of that table. `ev.Metric(label, 'column')` averages a BOOLEAN column
into a rate; hand it a fraction or a count and the run stops with
`TypeError: Need to pass bool-like values`.

That matters whenever the thing being scored lives INSIDE the output - findings
in a review, turns in a conversation, rows in an extraction. One case holds five
findings, so "how many located" is not a per-case yes/no. Say which of the two
you mean, because they are different measurements:

- per case, every case weighing the same -> a boolean column
  (`ev.Metric('all quotes locate', 'all_locate')`)
- pooled over items, every item weighing the same -> a callable
  (`ev.Metric('quotes locate', lambda d: d['n_ok'].sum() / d['n_findings'].sum())`)

Then list the columns the case function must return for that to be computable
(`n_findings`, `n_ok`, `all_locate`). Write them into the plan. A gate number no
listed column can produce is the single most common reason a finished plan cannot
be executed, and it is visible the moment the columns sit beside the gates.

**If the metric is a rate over a filtered subset, name its coverage metric here
too.** A filtered subset is gameable by shrinking it: quality over "the turns
where it said something" rises when it says something less often. A quality rate
without a coverage number beside it can move the right way for the wrong reason.
In an observed eval, output quality moving 31% to 100% only meant anything
because yield moved 1.62 to 2.42 in the same direction. Propose it as
`ev.Metric(..., coverage=ev.Metric(...))` so the runner prints coverage first.

**Name the BAR as reference points, not a gate.** What the baseline scores today,
and roughly where the user would act - written down before the run, because a
reference chosen after seeing the result is not one. It is not a pass/fail: real
results are mixed (one label up, another down), and the run ends in a written
judgement against these numbers, not a verdict computed from them. Prefer bars
RELATIVE to the baseline arm ("no worse than baseline on X") over absolute ones:
an absolute bar the baseline itself cannot reach measures the model, not the
change - observed, and rewritten after the fact.

**State the hypothesis test, and check the case count can resolve it.** The
verdict IS the test: H0 is that the arms are equal, the test is a paired bootstrap
of the difference clustered by case, and an interval spanning zero means no winner
is named (`inside noise`). So ask what the smallest difference worth acting on is,
then say whether the planned case count can see it. Roughly, at a 70% baseline
and one repeat:

| cases | +5pp | +10pp | +20pp |
|---|---|---|---|
| 20 | ~10% | ~15% | ~40% |
| 50 | ~10% | ~20% | ~70% |
| 100 | ~15% | ~35% | ~95% |
| 200 | ~20% | ~65% | ~100% |

Twenty cases resolve only a large difference. If the user cares about a 10-point
move, say in this answer where the extra cases come from - BEFORE anyone runs
anything. This is the most common reason an eval returns `inside noise` and feels
like a waste.

### Q5. What must not get worse - the guardrail?

Propose the OPPOSITE error as a second metric with a budget: if the metric is
"did it act", the guardrail is the false-positive rate on cases where the correct
behavior is to do nothing.

State it plainly: **without a guardrail, "act always" scores 100%.** A guardrail
is not optional here. A change that lifts the headline metric by acting on
everything is a regression that reports as a win, and only a control set catches
it. Propose it as `budget=` on an `ev.Metric(..., higher_is_better=False)`.

**Write the degenerate strategy as a sentence first, then read the guardrail back
against it.** "Without a guardrail, <strategy> scores 100%." If the strategy
still walks through the guardrail you just proposed, it is not a guardrail.

The failure to check for is a guardrail that is an ALGEBRAIC RESTATEMENT of the
metric. A metric of "quotes that locate >= 85%" beside a guardrail of "quotes
that do not locate <= 15%" is the same gate twice: it is satisfied by exactly the
arms that satisfy the metric, so nothing can ever fail it. The opposite error
here is padding output onto cases where the right answer was nothing - which is
why the guardrail needs the control cases in Q3's set, not a rearrangement of
Q2's number.

**Name the control cases the guardrail reads.** Cases where doing nothing is
correct, roughly a fifth of the set. Two or three cannot move a rate.

### Q6. Where do the cases come from, and how does the run launch?

**The case set needs a SOURCE, not a description.** "Documents across a range of
genres" is a rule for a good set; someone still has to produce it. Propose:

- **Sampled from real material** - from where, how many, how chosen, and the bias
  that introduces ("resolved tickets only" excludes every conversation that went
  badly, which is the population the eval most needs); or
- **Generated** - with the recipe written down: which model, the generation
  prompt, how many, what varies, and what stops them all being the same case in
  different words.

Say which cases are CONTROLS (doing nothing is correct - about a fifth of the
set, and Q5's guardrail reads them), which fixture files a case column points at
and whether they exist today, and any case whose text is embedded in a prompt
(that one is `holdout`, or it scores against its own answer key).

**The launch facts** - every eval in the repo runs from `evals/`, and
`evals/_env.py` is where these two land, once per repo (reuse it if it exists):

- **Credentials: where they live, and HOW they load** - the environment variable,
  secret store or file, and whether the loader resolves relative to the working
  directory. A loader that does will find nothing from `evals/`; the plan says
  which absolute path to load from instead. oryxflow never reads or stores a key.
  NEVER write a key, token or internal hostname into the plan file.
- **Where the production code lives, and how it becomes importable** - the
  package's directory and the `pyproject.toml` that owns it (often not the repo
  root), and whether it is installed (`pip install -e <dir>`) or needs a path
  added.

## 2b. The executability check - run it on your own six answers

A plan can settle exactly what to measure and still be impossible to run. Before
writing the file, walk your own answers against this list. Each item is a
sentence the plan must contain, not a judgement call - if you cannot write the
sentence, ASK rather than leaving it for the executor.

1. **The case set has a named SOURCE, not just rules.** Where the cases come
   from, how many, and who produces them. "Documents across a range of genres"
   describes a set nobody has made yet. Rules for a good set are worth keeping,
   but they are not a source.
2. **Real cases exist.** `synthetic` is arithmetic, not a label: the headline is
   averaged over rows where `synthetic` is falsy and invented cases print beside
   it. A rule that marks EVERY case synthetic leaves the headline reading `n/a`.
   If the set must start out invented, say what the headline is computed over
   until real cases land, and put it in `Known gaps`.
3. **Every input file exists or has an owner.** A case column holding
   `@fixtures/handbook.md` has promised a file. List them; say which exist.
4. **The model handle has an import path.** Not "two model families" - the module
   to import, the two model ids, and what makes that module importable from
   `evals/` (an installed package, or the path `_env.py` adds). One line, and it
   is the difference between executable and not.
5. **The table's unit and columns are written down** (Q4), every gate number
   names a column or a callable over the listed columns, and every gate is marked
   runnable NOW or BLOCKED on something nobody has written yet. If the headline
   gate is blocked, the plan says what runs today instead.
6. **The slots are budgeted.** The verdict renders THREE numbers: `coverage`,
   `metric`, `guardrail`, plus `slices=` breakdowns. A gate table with five rows
   must say which three take the slots and where the other two print - a second
   `ev.EvalResult(r.df, metric=...)` over the same frame, or report-only.
7. **Human labels have a per-case column** if the metric is judge-scored:
   `human=` reads a column of the case table, so it works only where one case
   carries one label.
8. **The guardrail beats the degenerate strategy** (Q5), and is not an algebraic
   restatement of the metric.
9. **The first run's shape is written down.** The `--check` line (run from
   `evals/`), the smoke run, and one line of what a correct result looks like. A
   wiring failure otherwise reads as a measurement.

Report which of the nine the plan satisfies and which it cannot yet, in one short
block. An item you cannot satisfy belongs in `Known gaps` with what would close
it - never silently dropped.

## 3. Write `evals/<name>/README.md` - and nothing else

Create the directory if needed, and write ONE file. Carry each answer's WHY into
the file: someone reading it in six months needs the reasoning, not just the
choice.

```markdown
# Eval: <name>

<One line: the change under evaluation and the failure it is chasing.>

## Goal

Decision: <who acts on this number, and what they do differently>.
Background: <what the surface does, who uses it, what a bad output costs>.
Today: <what ships now>, from `<base prompt path>`.
Failure chased: "<quoted from the real report>".
<Frequent failure, or the noticed one - one honest line.>

## Models

| role | model | why |
|---|---|---|
| under test | `<module:get_model>` -> `<pinned id>` | what production runs |
| judging | `<module:get_model>` -> `<pinned id>` | different family: <why> |

Reviewed by <who>: <their verdict on whether these fit the goal>.

## Prompts

`<module:function>` - the live entry point, reached from `<caller>`.
Reads `<template path>`. Production code, never a copy: <why>.

| arm | reads | cached on |
|---|---|---|
| `baseline` | `<paths>` at `<ref>` (`<sha10>`) | resolved sha of `<ref>` |
| `live` | `<paths>` in the working tree | hash of those files |

`ev.git_tree('<ref>', [<paths>])`. Not a string patch: <why>.

## Measure

`<label>` - <the one number>, computed from `<column>` produced by <what>.
Coverage: `<label>` - <why the subset needs one>. (Or: not a filtered rate.)
Bar (a reference for the written judgement, not a gate): baseline scores <value>
today; worth acting on at about <value>.
Test: paired bootstrap of the difference, clustered by case; an interval spanning
zero names no winner. Smallest difference worth acting on: <value>.
At <count> cases that is detectable about <value> of the time. <Enough, or where
the extra cases come from.>

### The table

One row per case, per arm, per repeat. The case function returns: `<col>`,
`<col>`, `<col>`.

| gate | reads | how | runnable |
|---|---|---|---|
| `<metric label>` | `<column>` | boolean column / callable over `<cols>` | now / blocked: <what is missing> |
| `<guardrail label>` | `<column>` | boolean column, budget `<value>` | now / blocked: <what is missing> |
| `<report-only number>` | `<column>` | printed by <where> | now / blocked: <what is missing> |

Runnable today: <the gates marked `now`>. Blocked: <the gates marked `blocked`,
and who produces what would unblock them>.

### Guardrail

`<label>`, budget `<value>` - <the opposite error>, over `<control cases>`.
Without it, `<degenerate strategy>` scores 100% on the measure above.

## Data

Source: <where the cases come from, and who produces them>.
<count> cases, <count> of them controls where doing nothing is correct.
Real vs synthetic: <what the headline is averaged over>.
Generated cases: <the recipe - model, prompt, what varies>. (Or: none.)
Fixtures: <which files a case column points at, and which exist today>.
Holdout: <any case whose text is embedded in a prompt>. (Or: none.)
Slices: `<column>`, `<column>`.

## Running it

Credentials: `<ENV_VAR>` / <secret store / file>, held by <who>; loaded <how - by
absolute path from evals/_env.py>. (Never the key itself.)
Production code: `<package>` in `<dir>`, importable by <`pip install -e <dir>` / a
path in evals/_env.py>.
First run, from `evals/`: `python run_eval_<name>.py --check`, then a 3-case smoke run.
A correct smoke result looks like: <one line>.

## Judgement calls

- <every decision made while answering the six questions, one line each>

## Known gaps

- <what this eval cannot see, and what would close it>
```

**The `runnable` column** in `The table` is what tells someone whether they can
start. Mark a gate `now` when every column it reads can be computed from the case
output and the material already in the repository. Mark it
`blocked: <what is missing>` when it needs something nobody has written yet - a
human answer key, a hand-labelled reference set, a fixture that does not exist.
Judge-scored gates are usually `now` for the raw rate and `blocked` for the
validated one, so say which you mean.

If the HEADLINE metric is blocked, say so in one line under the table and name
what runs today instead. A plan whose headline cannot be computed reads as
finished and stalls the first person who tries it.

**Judgement calls** is seeded from the conversation you just had: a metric that
was narrowed, a case class deliberately excluded, a proposal the user overrode,
a coverage metric judged unnecessary and why, a model choice the prompt owner
disagreed with. Write the ones that actually came
up; do not pad it.

**Known gaps** is honest, not defensive. Typical entries: no production export
yet so the cases will be synthetic; the guardrail control set is thin; latency
untracked; one arm only. An eval with no known gaps has not been thought about.

## 4. Report

Print the path of the one file written. Confirm no other file was created. Print
the step 2b result: which of the nine checks the plan satisfies, and which are
recorded as gaps.

Say the next step is `/oryxflow:eval-init`, which copies the scaffold, fills it
from this plan, and ends in a 3-call smoke run.

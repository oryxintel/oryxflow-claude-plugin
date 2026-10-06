---
description: Grow an eval case set from the placeholder rows to a real 15-25 - harvest genuine cases out of the repository first, say what could not be found, then propose the AXES that expose the untested gaps (controls, needs-user-input, mood pairs) and generate only the cases those axes require. Tags real vs synthetic, holds out any case whose text is in the prompt, and shows the diff before writing cases.csv.
disable-model-invocation: true
---

# Grow an eval case set to a real one

An eval scaffolded by `/oryxflow:eval-init` ships 3 placeholder cases. Three cases
is not a measurement. This command takes that set to a real 15-25 in three phases,
in this order: HARVEST what is real, PROPOSE axes, GENERATE only what the axes
require. Target directory: `${CLAUDE_PROJECT_DIR}`.

You write exactly two things: `evals/<name>/cases.csv`, and new files under
`evals/<name>/fixtures/`. Nothing else - not the metric, not the prompt, not
`eval.py`. If the harvest changes what should be measured, say so and point at
`/oryxflow:eval-plan`; do not edit the plan yourself.

Scope: an explicit `$ARGUMENTS` names the eval (a directory under `evals/`).
Otherwise find the eval directories yourself; if there is more than one, ask
which. If there is none, STOP - run `/oryxflow:eval-init` first.

## 1. Read what already exists

Read, before searching for anything:

- `evals/<name>/README.md` - the plan. It names the function under test, the
  metric, the guardrail and the baseline. The metric is what tells you whether a
  candidate case is even scorable; a case the metric cannot read is not a case.
- `evals/<name>/cases.csv` - the current header and rows, so your additions match
  the columns and you can tell placeholders from anything already harvested.
- The prompt or template under test, in full. You need its literal text for the
  holdout check in step 5, and its instructions tell you which behaviors are
  meant to be conditional (those are where the controls live).

## 2. Harvest real cases FIRST

Search the repository for genuine examples before inventing a single one. Real
places they hide:

- failure reports, bug tickets, incident notes, TODOs describing what went wrong
- test fixtures, recorded transcripts, snapshot files, golden outputs
- quotes and worked examples inside requirements or specification documents
- any exported log, dump or sample of production traffic
- commit messages and PR descriptions for the change that motivated the eval

Search by shape, not by one guessed filename - grep for the vocabulary of the
surface under test across `docs/`, `tests/`, `fixtures/` and the issue notes, and
list the directories before grepping so you do not miss an obvious one.

Take real cases VERBATIM. Lightly sanitizing an identifier is fine; rewriting the
phrasing is not - the phrasing is the data. If an input is long, write it to
`evals/<name>/fixtures/<case>.md` and reference it from the CSV as
`@fixtures/<case>.md`; the loader substitutes the file's text, resolved relative
to the case file. That is what keeps a flat CSV usable with realistic inputs.

## 3. Report the harvest - including what is NOT there

Say what you found and exactly where each came from (`file:line`). Then say
plainly what you could NOT find. This half is not optional and it is not a
disclaimer - it is the finding that decides the next step.

If there is no export of real traffic, ASK FOR ONE. Do not substitute invention
for it and move on:

> I found 6 real cases (4 in `tests/fixtures/`, 2 quoted in the failure report).
> I found no export of real user turns - nothing in the repo carries production
> phrasing. If you can drop even 20 raw turns into `evals/<name>/fixtures/`, they
> are worth more than anything I can invent. Want to do that first, or should I
> proceed with synthetic cases on top of the 6?

Wait for the answer. A set built on 6 real cases plus acknowledged synthetics is
honest; the same set with the gap unmentioned is not.

## 4. Propose AXES, not cases

Naming the axes is the design - the cases fall out of it. Do not present a flat
list of failure examples: a flat list distinguishes nothing. Crossing a phrasing
axis against a state axis is what separates a WORDING problem from a CONTEXT
problem, and that separation is the whole reason a report can slice.

Derive each axis from a gap you can point at in the real set. Show the gap:

> All 6 real cases arrive with full context, so nothing tests the empty state.
> All 6 are imperative, so mood is untested. None of them should result in no
> action, so there are no controls at all.

Then propose the axes as a table with the values and what each one buys. A
generic shape:

| Axis | Values | The gap it closes |
|---|---|---|
| `phrasing` | `imperative`, `question` | Isolates wording from meaning |
| `state` | `full`, `partial`, `empty` | Whether needed context is present |
| `expected_action` | `act`, `none`, `ask` | Whether acting is correct at all |

Cases are the cross of the axes, pruned to the combinations that can actually
occur, plus the real cases slotted into whichever cell they already occupy.
2 x 3 x 3 pruned lands in the 15-25 band without padding.

Every axis MUST become a real column in `cases.csv`. The loader routes any column
it does not recognize into case metadata, which becomes a DataFrame column and is
therefore a report slice - so an axis that is only in your head produces no
per-slice breakdown, and the design was for nothing.

## 5. Two checks on EVERY generated case

Both of these are observed failures in real harnesses, not hypotheticals. Run
them before a case is written, and drop or repair any case that fails one.

**a. Would a correct model actually have to act here?** Read the case's own
fixture and ask whether the requested change is already satisfied by it. If it
is, a correct refusal scores as a failure - the model was right and the eval was
wrong. This has happened; it makes a good prompt look broken. Either alter the
fixture so the work is genuinely outstanding, or reclassify the row as a control
and score it that way deliberately.

**b. Does this text appear in the prompt?** Grep the prompt and its templates for
the case's literal wording. If a case is quoted in the instructions, tag it
`holdout=1`. Held-out cases are excluded from EVERY arm - otherwise the
comparison is scored against its own answer key, and the arm containing the
example wins for free. Keep the row in the file with the tag; deleting it loses
the record that it was considered.

## 6. Three categories to propose BY NAME

Each catches a distinct failure. A set missing one is not obviously wrong - it is
silently weaker, which is worse. Name all three in the proposal so the user can
decline one on purpose rather than never hear about it.

- **Controls.** Cases where the correct behavior is to DO NOTHING. Without them a
  prompt that acts on everything scores perfectly, and "act more" is the easiest
  accidental change to make. Controls are what turn the guardrail from a number
  into a measurement. Aim for roughly a quarter of the set.
- **The needs-user-input trap.** A request the assistant genuinely cannot fulfil
  without something only the user has - a file it has no access to, a decision
  only they can make, a credential. The correct behavior is usually to ASK in the
  main response while still doing whatever useful work is available elsewhere. So
  this case is the one that distinguishes "handled it properly" from "punted",
  which no other case in the set can see.
- **The mood pair.** The same semantic request twice: once imperative, once as a
  question. Real harnesses keep finding that phrasing alone flips behavior. A
  uniformly imperative set cannot see it, and the two rows share every other axis
  value, so the difference between them has exactly one explanation.

## 7. The CSV format

`ev.load_cases(path, inputs=Model)` routes columns by NAME, no configuration:

- `name` - the case name
- a field of the `inputs` model - that input field, validated by pydantic (so a
  typo'd column is an error naming the field, not a silent default)
- `expected` / `expected.*` - the expected output
- everything else - metadata, which becomes a DataFrame column and a report slice

Rules that follow from that:

- A value of the form `@fixtures/doc.md` is replaced by that file's text,
  resolved relative to the case file.
- Reserved metadata columns: `synthetic`, `holdout`, `expect_*`, and **`arm`**.
  Do not reuse those names for an axis. `arm` is the label the sweep gives each
  cell of the matrix, so a column of that name is refused outright - if the
  natural word for your axis is "arm" (an `outline` arm vs a `guidelines` arm),
  call the column `surface`, `variant` or `write_arm` instead.
- Booleans accept `true/false/yes/no/1/0`.
- Your axis names are ordinary metadata columns - keep them short, snake_case,
  and stable, because they are what the per-slice breakdown is keyed on.

**`synthetic` is mandatory on every row**: `synthetic=0` on everything harvested,
`synthetic=1` on everything invented. NEVER blend them into one number. The
headline metric is REAL-ONLY, with the synthetic result reported beside it - a
synthetic set written by the same mind that wrote the prompt flatters it, and a
blended rate hides exactly how much of the score is self-graded.

The flag tracks where the CONTENT came from, not whether a model was involved
in producing the row. An LLM that selects, trims or reformats real material -
pulling ten threads out of a support log, cutting a document down to the
section under test - yields REAL cases (`synthetic=0`); an LLM that writes the
material yields synthetic ones (`synthetic=1`). Read it the other way and every
harvested case gets `synthetic=1`, which leaves the real-only headline with
nothing to average and printing `n/a`.

## 8. Show the diff, then write

Show the proposed additions BEFORE touching the file: the axis table, the counts
(real vs synthetic, controls, holdouts, total), and the new rows in a readable
form - truncate the long inputs in the display, never in the file.

Then offer three options, in these words:

> `show me` - print the full text of every new case
> `yes` - write them to `cases.csv`
> `adjust axes` - change the axes and regenerate

On `yes`, APPEND to `cases.csv`. Never overwrite an existing row and never drop
one. Remove a placeholder row only when a real case supersedes it, and say which.
Write fixture files first, then the CSV, so no row ever references a file that is
not there.

Once the set is real - every placeholder row superseded and the categories in
section 6 present - delete the `PLACEHOLDER SCAFFOLD` marker line from `eval.py`.
That marker means "this eval still runs on placeholder cases", so leaving it on a
real set makes `/oryxflow:check-standards` report a finished eval as unfinished
forever. If placeholder rows remain, LEAVE the marker and say which rows still
need replacing.

## 9. Report

Close with the counts by category (real, synthetic, controls, holdouts, total),
the axes now present as sliceable columns, and any gap you could not close - a
state with no real example, an axis you proposed and the user declined. Name it;
it belongs in the "known gaps" section of `evals/<name>/README.md` and the user
should know to put it there.

Next step: `/oryxflow:eval-run` to score the arms against the new set.

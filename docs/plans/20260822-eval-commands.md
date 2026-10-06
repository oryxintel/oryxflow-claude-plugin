# Eval commands: `eval-plan` / `eval-init` / `eval-cases` / `eval-run`

> Depends on the library work in the oryxflow repo:
> `docs/todo/20260822-evals-llm-eval-harness.md` (the `oryxflow.evals` API these commands drive)
> and `docs/todo/20260822-engine-computed-code-version.md` (prompt edits invalidate their arms).
> Do not implement these commands before `oryxflow.evals` exists — every transcript below calls it.

## Context

An AI engineer changes a prompt and does not know whether it is better. That is the moment this
feature exists for, and today the agent handles it badly in two distinct ways, both observed:

**It writes a throwaway probe.** Asked to validate a prompt change, the agent produced a one-off
script that fires a handful of turns and prints the output for a human to read in bulk. That is not
a measurement: no baseline, no metric, no controls, no record, nothing to re-run next month. It
also correctly reported that it could not validate the wording — which is the right answer given the
tools it had, and the wrong outcome.

**Or it bypasses oryxflow entirely.** Asked for a *quick* eval, an agent inspected an existing
oryxflow-based eval in the same repository and chose not to use it — *"no oryxflow caching — quick
run, plain asyncio."* Its instincts about method were good (it built a byte-exact baseline arm from
git history, a deterministic metric plus a guardrail, and an LLM judge for the fuzzy part); what it
rejected was the ceremony. It then paid full price for every case on every iteration of the workload
that iterates most.

Both failures are the same failure: **there is no cheap, obvious, well-lit path from "I changed a
prompt" to "here is a defensible number."** The library plan supplies the machinery. This plan
supplies the path, and the method that makes the numbers mean something.

The method is the part a library cannot ship. Reading real eval harnesses, the decisions that
separate a useful eval from a misleading one are all judgement:

- A guardrail is mandatory. A change that improves "did the assistant act" by acting on everything
  scores 100% and ships a regression; only a control set catches it.
- **A quality rate is read after a coverage metric, never alone.** A rate over a filtered subset is
  gameable by shrinking the subset — one prompt scored respectably on output *quality* largely by
  staying silent on a third of turns. Quality moving 31% to 100% only meant something because yield
  moved 1.62 to 2.42 in the same direction.
- Cases must be genuine. One harness scored correct refusals as failures because its fixture asked
  for a change that had already been made — the model was right and the eval was wrong.
- Synthetic cases never join the headline. A set written by the same mind that wrote the prompt
  flatters it.
- Any case whose text is embedded in the prompt is held out of **every** arm, or the comparison is
  scored against its own answer key.
- **The baseline is checked out of git, not reconstructed by string replacement.** An earlier draft
  of this plan said anchored diffs; a real harness found the limit — two of four template changes
  were *deletions*, and a replacement cannot put a deleted section back where it was. Anchored diffs
  remain right for a *probe* (a rewrite not yet shipped, which must raise when its anchor is gone);
  a ref is right for a *baseline*.
- **Nothing between the model's output and the scorer.** A harness capped its output field at 2000
  characters for CSV readability, and its metric read the last line of that field — so it sliced
  long replies mid-sentence and scored the model down for the harness's own scissors.
- **The judge is a different model family from the model under test, grades raw output, and has no
  optional fields.** Self-preference is real and avoiding it is free; grading post-sanitizer output
  measures the backstop rather than the prompt; and an optional flag is one the model can decline to
  fill, which reads downstream as a pass.
- **A metric identically dead in every arm is measuring the harness.** 0% before and 0% after is
  almost never a model result. Check the metric's inputs before reading anything else — this is the
  heuristic that caught the truncation bug above.

### Design decisions

**1. Four commands, grouped under `eval-`.** `eval-plan`, `eval-init`, `eval-cases`, `eval-run`.
Typing `/oryxflow:eval` surfaces all four, which is the discovery argument. This inverts the
plugin's existing `<verb>-<noun>` convention (`init-project`, `check-standards`); accepted
deliberately, because evals are the only multi-command suite and the grouping is worth more than
the consistency here. Note the inversion in the plugin `CLAUDE.md` so it reads as a decision rather
than an oversight.

**2. Deciding and generating are separate commands.** `eval-plan` writes a plan and no code;
`eval-init` copies files. This restores the meaning `init-*` has elsewhere in the plugin ("copies
files"), and it mirrors the library's own `preview` / `run` pairing, so the relationship is already
familiar. `eval-init` run with no plan present does the plan step inline and waits for confirmation
before writing anything, so the extra step never blocks anyone.

**3. The plan is a durable artifact, not a wizard transcript.** `eval-plan` writes
`evals/<name>/README.md` recording what is measured, the guardrail, the baseline, and the known
gaps. Real hand-written harnesses all have this document and it is what makes them re-readable six
months later; generating it first means the eval is documented by construction.

**4. All four are `disable-model-invocation: true`.** Two write files; `eval-run` bills the user.
The skill may *suggest* running one, in words, but never invokes it.

**5. No eval spends money without showing the bill.** Every `eval-run` prints the projected call
count, the cached/new split and an estimated cost, and waits, unless the user passed `--yes`.

**6. Rejected: an `eval-compare` command.** Comparison is what `eval-run` already prints, and
across time it is a cache read rather than a new run. A fifth command would earn nothing.

**7. The quick path is the cached path.** The skill states explicitly that a "quick eval" is
`ev.sweep(fn, ...)` in a scratch file — six lines, no scaffold — and that hand-rolling `asyncio`
costs the full bill again on every iteration. This is a named rule because the failure it prevents
was observed, not imagined.

## Execution

### Branch — and the one hard rule for this repo

This is the **third** of three related plans. The first two live in the sibling `oryxflow` library
repo and must both be verified first, because every transcript below calls the API they build:

1. `<oryxflow repo>/docs/todo/20260822-engine-computed-code-version.md`
2. `<oryxflow repo>/docs/todo/20260822-evals-llm-eval-harness.md`
3. `docs/plans/20260822-eval-commands.md` — this file.

```bash
cd <plugin repo root>
git checkout main && git pull
git checkout -b 20260822-evals
```

**NEVER commit or push this repository.** Editing its files is expected; committing them is not —
the maintainer commits this repo themselves. Creating the branch is fine; leave every change in the
working tree. This also means **no `version` bump in `.claude-plugin/plugin.json`**: changelog
bullets go under `## [Unreleased]` and the maintainer cuts the release.

Iterate with `claude --plugin-dir <plugin repo>` and `/reload-plugins` after each edit — an
*installed* copy will not pick up your changes, so do not test that way.

### Subagent orchestration

Fan out with the Agent tool, file-disjoint per wave. Every prompt carries: this plan's absolute
path, the section it owns, its exclusive file list, the **method bullets from the Context section
above** (they are the content, not background), the rule *"do not create or edit any file outside
your list"*, and the rule *"never run `git commit` or `git push` in this repository."*

**Wave 1 — four agents in parallel, one command file each:**

| Agent | Section | Exclusive file |
|---|---|---|
| A | 1 | `commands/eval-plan.md` |
| B | 2 | `commands/eval-init.md` |
| C | 3 | `commands/eval-cases.md` |
| D | 4 | `commands/eval-run.md` |

Agent B must copy the platform-specific copy commands and the robocopy exit-code caveat from
`commands/init-project.md` **verbatim** rather than re-deriving them; that wording exists because
robocopy's success codes were repeatedly misread as failures.

**Wave 2 — two agents in parallel:**

| Agent | Section | Exclusive files |
|---|---|---|
| E · template | 5 | `resources/template-eval/*` |
| F · skill | 6 | `skills/oryxflow/evals.md`, `skills/oryxflow/SKILL.md` |

Agent F carries the largest share of the value in this plan: `evals.md` is the method, and the
quick-eval rule in `SKILL.md` is what prevents the observed bypass. Give it the full Context section.

**Wave 3 — one agent:** section 7 — `README.md`, `docs/CHANGELOG.md`, and the `CLAUDE.md` note
recording the `eval-*` naming inversion as a decision.

**Wave 4 — you, not an agent:** the entire Verification section. It is interactive by nature (the
commands are prompts, and the failure modes are behavioral), and steps 9, 10 and 11 are the
acceptance tests for the whole feature. A subagent cannot run them meaningfully.

## Implementation

### 1. `commands/eval-plan.md`

Frontmatter: `description`, `disable-model-invocation: true`.

Behavior: gather context, then ask four questions with proposed answers drawn from the repository —
the questions are fixed, the proposals are whatever is actually there.

Context to gather first (shell + read, not guesswork): the working-tree diff and recent commits
touching prompt/template files; the call path from the changed file to its entry point; any failure
report, ticket or note in the repo describing what went wrong; whether an `evals/` directory already
exists.

The four questions, each presented with a proposal and a one-line justification:

1. **What is the function under test?** Propose the live entry point from the call path. State the
   rule: production code, never a copy — a second copy of the instructions in the eval directory
   drifts and then measures nothing.
2. **What is the metric — the one number that answers "is it better"?** Derive from the failure
   being chased: a silent failure means *did it act*; a wrong answer means *is it right*; a slow
   one means latency. Warn against LLM-as-judge when the output is one of a fixed set of labels.
   **If the metric is a rate over a filtered subset, name its coverage metric here too** — the
   subset is gameable by shrinking it, and a quality rate without a coverage number beside it can
   move the right way for the wrong reason.
3. **What must not get worse — the guardrail?** Propose the opposite error. State plainly that
   without it, "act always" scores 100%.
4. **What is the baseline to beat?** Propose a git ref — the commit before the change — materialized
   with `ev.git_tree(ref, paths)`, not a string patch of the live files. Say why in one line: a
   replacement cannot restore a section the change deleted, and it decays silently when the live
   template moves.

Then write `evals/<name>/README.md` with those four answers, a "judgement calls" section seeded
with anything decided while answering the four questions, and a "known gaps" section. Print the path. Say the
next step is `/oryxflow:eval-init`. Write no other file.

### 2. `commands/eval-init.md`

Frontmatter: `description`, `disable-model-invocation: true`.

1. If `evals/<name>/README.md` does not exist, run the `eval-plan` flow inline, show the plan, and
   wait for a yes before writing anything.
2. Copy `${CLAUDE_PLUGIN_ROOT}/resources/template-eval/` into `evals/<name>/`, skip-existing, never
   overwriting. Use the same platform-specific copy commands and the same robocopy exit-code caveat
   as `commands/init-project.md` — reuse that wording verbatim rather than re-deriving it.
3. Fill the template from the plan: the metric and guardrail declarations, the arm parameters, the
   import of the function under test.
4. Ensure `oryxflow[evals]` is installed; if not, print the exact install command for the project's
   environment and stop.
5. **Smoke run**: 3 cases, 1 arm, 1 rep — about three API calls. This proves credentials and wiring
   before anyone commits to a sweep, and it is the structural answer to the silent-credential
   failure where every case raises and an empty result caches as a measurement.
6. Report created vs skipped files, then close honestly: *"3 cases is not a measurement — run
   `/oryxflow:eval-cases` to get to 15-25."*

### 3. `commands/eval-cases.md`

Frontmatter: `description`, `disable-model-invocation: true`.

**Harvest real first.** Search the repository for genuine examples: failure reports and tickets,
test fixtures and transcripts, quotes in requirements documents, any exported log. Report what was
found and where, and say plainly what was *not* found — if there is no production export, ask for
one rather than substituting invention for it.

**Then propose axes, not cases.** Naming the axes is the design; the cases fall out of it. Crossing
a phrasing axis against a state axis is what distinguishes a wording problem from a context problem,
where a flat list of failures distinguishes nothing. Show the gaps in the real set that motivate
each axis (all cases have full context, so nothing tests the empty state; all are imperative, so
mood is untested; there are no controls at all).

**Two checks on every generated case**, both learned from real harnesses:

- *Would a correct model actually have to act here?* A case asking for a change that is already
  made scores a correct refusal as a failure.
- *Does this text appear in the prompt?* If so, tag `holdout=1` — excluded from every arm.

**Three case categories to propose by name**, because each catches a distinct failure and a set
missing one is silently weaker:

- **Controls** — cases where the correct behavior is to do nothing. Without them a prompt that acts
  on everything scores perfectly.
- **The needs-user-input trap** — a request the assistant genuinely cannot fulfil without something
  only the user has. The correct behavior is usually to ask in the main response while still doing
  something useful elsewhere, so this case distinguishes "handled it properly" from "punted".
- **The mood pair** — the same semantic request as an imperative and as a question. Real harnesses
  keep finding that phrasing alone flips behavior, and a set that is uniformly imperative cannot
  see it.

Write to `cases.csv` with `synthetic=1` on everything invented and `synthetic=0` on everything
harvested. Never blend: the headline metric is real-only, synthetic reported beside it. Show the
diff before writing; offer `show me / yes / adjust axes`.

### 4. `commands/eval-run.md`

Frontmatter: `description`, `disable-model-invocation: true`.

1. Determine the arms — from the user's argument (`prod vs preship`), or from the plan's baseline
   when none is given.
2. Print the bill: cases x arms x reps, the cached/new split, estimated cost and duration. State
   *why* a cell is new (an arm never run, or a prompt changed since it last ran). Wait for
   confirmation whenever uncached cells exist.
3. Run via `oryxflow.evals`, print the verdict block, write `results/<date>-<arms>.md`.
4. **Check the harness before believing the numbers.** If the library printed a dead-metric flag
   (a metric identically 0% or 100% in every arm) or a denominator-drift line, investigate that
   *first* and say so — do not narrate a result sitting on top of it. Read one full raw output for
   a case the metric marked as failing and confirm the metric is reading what you think it reads.
   The observed instance of this was a display cap slicing the field the metric was computed from;
   it presented as a plausible model failure and was an eval artifact.
5. **Then diagnose.** This is the part no library can do and the part real reports do well: read
   the failing rows, name the mechanism, quote the evidence, and propose the next arm with its
   cost. Follow the observed-good pattern of reporting a mixed result straight — a targeted fix
   that improved two labels and regressed a third is a mixed result, not a win. Report residual
   weaknesses that remain in the winning arm rather than closing on the headline.
6. Never restate a verdict more confidently than the library's. If the delta sits inside the
   interval, the answer is "inside noise at N reps; raise repeats before calling this real" — not a
   winner.

With no arguments in an existing eval directory, `eval-run` reports what changed since the last run
and offers to re-run only the stale arms.

### 5. `resources/template-eval/`

Files copied by `eval-init`:

```
cases.csv          # header + 3 placeholder rows, incl. one control and the synthetic column
fixtures/.gitkeep  # @-referenced blobs
agent.py           # the function under test — imports PRODUCTION code, with a comment saying why
eval.py            # the TaskEval: params, metric, guardrail, slices, code_version()
run_eval.py        # three lines: import the task, call ev.cli(Task)
results/.gitkeep
README.md          # written by eval-plan, not copied
```

`eval.py` carries a `PLACEHOLDER SCAFFOLD` marker in the same style as `template-minimal/tasks.py`,
so `check-standards` and `update-project` can recognize an unfinished eval.

### 6. `skills/oryxflow/SKILL.md` + a new `skills/oryxflow/evals.md`

`SKILL.md` gains a short trigger section pointing at `evals.md`, loaded on demand (same pattern as
`ml-patterns.md`), plus two behaviors:

- **The quick-eval rule.** When asked for a quick eval, the quick path is `ev.sweep(fn, ...)` in a
  scratch file — six lines, no class, no scaffold, cached. Do not hand-roll `asyncio.gather`: a
  quick eval is the one you re-run most, so an uncached run re-bills every case on every iteration.
  Reach for `/oryxflow:eval-init` when the eval is worth keeping, not before.
- **Stale-arm awareness.** After editing a prompt or template in a repo containing an `evals/`
  directory, say so and name the cost:
  > *I changed `<template>`. There is an eval for this surface (`evals/<name>/`) and its `<arm>`
  > arm is now stale — `/oryxflow:eval-run` re-runs N calls (about $X). Worth it before trusting
  > the wording.*

  Suggest; never invoke. This is the moment the whole feature exists for.

`evals.md` carries the method: the four questions; the mandatory guardrail; coverage-before-quality;
real vs synthetic; holdout; the git-ref baseline and when an anchored probe is right instead; judge
rules (different model family, raw output, no optional fields); the no-transformation-before-the-
scorer rule; the dead-metric heuristic; when to raise repeats; and the reading of a verdict that
sits inside the noise. Agent-facing, so it may be more technical than the user docs — but still
verbs over mechanisms.

### 7. Plugin housekeeping

- `README.md` — the four commands in the quickstart list and in the commands section.
- `docs/CHANGELOG.md` — bullets under `## [Unreleased]`. Leave `plugin.json` at its last released
  version; the maintainer cuts the release.
- `.claude-plugin/plugin.json` — **no version bump in this work.**

## Files modified

| File | Change |
|---|---|
| `commands/eval-plan.md` | new |
| `commands/eval-init.md` | new |
| `commands/eval-cases.md` | new |
| `commands/eval-run.md` | new |
| `resources/template-eval/*` | new template directory |
| `skills/oryxflow/SKILL.md` | quick-eval rule, stale-arm behavior, pointer to `evals.md` |
| `skills/oryxflow/evals.md` | new — the method |
| `README.md` | the four commands |
| `docs/CHANGELOG.md` | Unreleased bullets |
| `CLAUDE.md` | note the `eval-*` naming inversion as a decision |

## Verification

The plugin has no test suite, so verification is a scripted manual pass in a throwaway project with
`claude --plugin-dir <repo>` and `/reload-plugins`:

1. `/plugin validate .` passes with the four new commands.
2. In a project with a prompt template and no `evals/`: `/oryxflow:eval-plan` asks the four
   questions with proposals drawn from the actual diff, and writes **only** `evals/<name>/README.md`.
3. `/oryxflow:eval-init` copies the template, fills it from the plan, overwrites nothing, and ends
   with a 3-call smoke run that surfaces a credential failure as an error rather than an empty
   result. Verify the failure path by deliberately unsetting the key.
4. `/oryxflow:eval-init` in a project with no plan runs the plan inline and waits before writing.
5. `/oryxflow:eval-cases` finds the real examples that exist, says what it could not find, proposes
   axes rather than a case list, and tags `synthetic` correctly. Verify it refuses to write a case
   whose requested change is already satisfied by the fixture.
6. `/oryxflow:eval-run` prints the bill and waits; `--yes` skips. Confirm cached cells cost nothing
   on a second run, and that editing the template makes only the affected arm stale.
7. Verdict honesty: construct an arm pair whose difference is inside the noise and confirm the
   agent reports "inside noise", not a winner. Construct one that improves the metric and breaks the
   guardrail and confirm it reports "not a clean win".
8. Skill behavior: edit a prompt in a project with an `evals/` directory and confirm the agent
   volunteers the stale-arm line with a cost, and does **not** run anything.
9. Quick-eval rule: ask for "a quick eval" in a project with no `evals/` directory and confirm the
   agent reaches for `ev.sweep(fn, ...)` rather than writing a bespoke asyncio script.
10. Harness-first discipline: rig a metric to read a deliberately truncated field so it scores 0%
    in both arms, and confirm the agent investigates the dead-metric flag **before** narrating any
    result. This is the failure that cost a real run and was caught only by a human noticing the
    two zeros.
11. Baseline fidelity: on a change that **deleted** a template section, confirm `eval-plan` proposes
    `git_tree` and that the agent does not offer a string-replacement variant as the baseline.

Step 9 is the acceptance test for this plan: it is the exact prompt that previously produced
*"no oryxflow caching — quick run, plain asyncio."* Step 10 is the acceptance test for the method:
the agent's job is to distrust its own instrument before it interprets a number.

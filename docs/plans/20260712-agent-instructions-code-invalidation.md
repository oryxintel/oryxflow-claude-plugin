# Plan: rewrite the plugin's agent-interaction instructions for v4 code-invalidation

## Context

The engine ships v4 (`oryxflow/docs/todo/20260712-engine-code-invalidation-v4.md`):
per-task `code_version`, AST-transitive advisory hashing, `accept_code()`,
`keep_versions`, and an append-only event stream with `oryxflow.events.status()` /
`runs()`. The plugin's current agent guidance in `skills/oryxflow/SKILL.md`
predates this and is written for the pre-v4 world:

- `flow.reset(tasks.X)` framed as "the ONLY reset path" for a code change
  (SKILL.md ~L577-584).
- Keep `flow.reset(...)` lines as commented toggles in `run.py` (~L288-290, L585-589).
- The per-param-variant staleness gotcha + `runLoad(..., reset=True)` workaround
  (~L605-618).
- "Confirm a reset took" via `RunResult.summary()` / `did_run()` (~L643-665).

Under v4 the primary idiom becomes **edit -> bump `code_version` -> run**, with the
staleness warning as the net when the bump is forgotten, and the event log as the
memory/provenance layer. This plan specifies how to rewrite the plugin's
agent-facing instructions for that world, written from the perspective of the
consuming agent (what instructions are actually followable), and preserves an
**FAQ** built from the seven trust concerns + the decision table (they are the
highest-value quick-reference; keep them).

Scope: docs/instructions only (SKILL.md, reference.md, conventions.md, the
CLAUDE.md snippet). No engine or code changes here; those live in the engine v4
plan and its step 9 (which this plan is the detailed version of).

## Design stance (why the instructions get written this way)

Instructions an agent will actually follow obey four rules, learned from the v4
evaluation:

1. **Fire at the decision point; do not rely on recall.** The single most reliable
   instruction is one attached to the moment of the action (bump in the SAME edit;
   answer a warning the moment it fires), not a rule to remember later. Prose an
   agent must hold across a session gets dropped.
2. **A decision table beats paragraphs.** v4 introduces four+ verbs
   (`Parameter` / bump / `accept_code` / `reset`). The confusion is never one verb
   in isolation - it is "which do I reach for". One table resolves it; scattered
   prose does not.
3. **One session-start call, not three.** After `/clear` an agent should hit a
   single entry point (`events.status()`) rather than composing queries or grepping
   stdout.
4. **Degrade gracefully.** Most existing projects (e.g. the benchmark pipeline) carry
   NO `code_version` yet. The instructions must stay correct for un-adopted tasks
   (where reset is still the path and there is no warning net) while pushing the
   bump-based workflow as the target state. Never imply the warning protects a task
   that has not adopted `code_version`.

Primary shift to state plainly: **bump `code_version`, do not hand-chain resets, for
code changes.** `reset()` remains valid and is still the ONLY reset primitive (do
not write reset helpers) - but its role narrows to: delete outputs, force a
recompute the fingerprint cannot detect (changed input data, corrupt cache), and the
one-time first-add case.

One concrete win to highlight (it retires an old gotcha): the code fingerprint is
`md5(family, code_version, sorted dep fingerprints)` - **params are not in it**. So a
single `code_version` bump invalidates EVERY parameter instance of that task by
identity (each variant's stored record mismatches the new fingerprint). The old
"reset only recomputes the variant you name; other `env`/param variants stay stale;
use `runLoad(reset=True)` per variant" hazard is **solved** by bumping - all variants
rerun when next built. The instructions should replace that workaround with this.

## What changes, per file

### 1. `skills/oryxflow/SKILL.md` (the main rewrite)

Replace the reset-centric "modified a task" section (~L577-620) and the
confirm-a-reset subsection (~L643-665) with the v4 workflow below. Keep the
"`flow.reset` is the only reset primitive; do not write a reset helper" rule - it is
still true. Reframe the `run.py` commented-toggle pattern: it is now for the
reset-only cases (input data changed, corrupt cache), not for code edits (those are
a bump, no toggle).

Insert, in the order an agent meets them:

**A. Session start / after `/clear` (new, top of the workflow section).**
```
Call oryxflow.events.status() before assuming anything about cache state. It returns
{pending_warnings, last_runs per family, recent_failures} in one call - pending code
warnings you must resolve, what ran last, and recent failures. No-Python fallback:
tail -30 .oryxflow/events.jsonl.
```

**B. The verb decision table (the centerpiece - lift verbatim from the engine v4
appendix).**

| I changed... | Do this | Why |
|---|---|---|
| a value/knob that is a `Parameter` | nothing | new identity auto-reruns; old output kept side-by-side |
| logic (this task's `run()` or a helper it imports), output will differ | bump `code_version` | propagates downstream, recomputes; invalidates ALL param variants at once |
| code, but output is provably identical (rename, extract, log line) | `accept_code()` - only if certain; when unsure, bump | re-stamps without recompute; the one non-recomputing exit |
| an external input the pipeline reads (raw data file, API response) | `reset()` the loader/source task that ingests it | invisible to the fingerprint; reset at the ingestion point (a downstream reset reloads cached old data) |
| nothing the system can see, but I need a fresh compute (suspect/corrupt cache) | `reset()` | forces recompute when no fingerprint moved |
| I want the outputs gone | `reset()` | delete |
| first time adding `code_version` to a task I ALSO just edited | bump AND `reset()` once (or add it in an edit-free change first) | grandfathering would otherwise bless stale output |

**C. Workflow rules (prose, terse, each tied to its moment).**
- When you change a task's logic (its `run()` or a helper module it imports), bump
  that task's `code_version` IN THE SAME EDIT. Do not hand-chain `reset()` for code
  changes - the bump propagates downstream automatically and invalidates every param
  variant.
- First time adding `code_version` to a task: if you are adding it BECAUSE you just
  changed the code, also `reset()` that task once (grandfathering treats existing
  output as current; the mtime guard warns but do not rely on it). Cleaner: adopt
  `code_version` across the project in an edit-free change first, then future edits
  are clean bumps.
- Answer every staleness warning with one of its three exits: **bump** (semantic
  change) / **`accept_code(TaskX)`** (output-equivalent refactor - only if certain;
  when unsure, bump, recompute is cheap insurance) / **`reset`** (recompute
  regardless). Never leave a warning firing across runs.
- Verify an invalidation took: after a bump/reset, the next run must show the task in
  `result.ran` (or `events.runs()`) with the matching reason (`code change (1 -> 2)`).
  `ran=0` after an intended invalidation is a BUG (the change did not reach the
  cache), not a convenient skip. `ran=0` on an untouched pipeline is the healthy
  "cache trusted" signal.
- "The numbers changed and I don't know why": `oryxflow.events.runs(task_family=
  'TaskX', last=2)` and diff params, code_version, source_hashes.
- Log decision-relevant scalars inside `run()` via `self.logger.info(...)` - v4
  captures them as `task_log` events, so they become next session's queryable memory
  (not lost stderr).
- Experiments side by side: string version (`code_version = 'v2-log-features'`) +
  `keep_versions = True` keeps old versions at readable paths. But if the thing you
  are varying is a VALUE, make it a `Parameter` instead - params already give
  side-by-side outputs and auto-rerun. Use code_version experiments for LOGIC
  variants you want to keep, not value sweeps.
- Raw stream: current = `.oryxflow/events.jsonl` (stable head); offloaded months =
  `events-YYYYMM.jsonl`; all history = glob `events*.jsonl`. Prefer
  `events.runs()`/`status()` when Python is available.

**D. The RunResult update.** Keep the existing `result.did_run()` / `.summary()` /
`.ran` / `.complete` guidance (still valid) and ADD: `result.reasons` (why each task
ran), `result.warnings` (unacknowledged code changes), `result.run_id`;
`MultiRunResult` exposes `ran`/`complete`/`failed`/`reasons`/`warnings` flattened
across flows - never hand-roll `sum(len(r.ran) ...)`. Note that scripts typically
discard the result, so the durable check is `events.status()` after the run.

### 2. `skills/oryxflow/reference.md`

Add an API-surface subsection: the `code_version` class attribute (str or int),
`keep_versions`, `oryxflow.accept_code(task=None)`, `oryxflow.events.status()` /
`runs(task_family, last)` / `iter_events()`, the `RunResult`/`MultiRunResult` new
accessors, and the `.oryxflow/` layout (events.jsonl head/offload, index.db is a
rebuildable derived cache - never edit it, delete-to-rebuild). State the advisory
honesty explicitly: the hash is advisory only and has blind spots (data-file
contents, external APIs, dynamic imports) - a cache hit is not proof of freshness for
those; that is what the "changed external input -> reset the loader" table row is for.

### 3. `skills/oryxflow/conventions.md`

The existing "log scalars with `self.logger` inside `run()`" convention gains a
second, stronger motivation: those lines are now captured as `task_log` events and
become cross-session memory - so the habit is no longer just for a live run's log, it
is how an agent remembers what it learned. Add a one-liner and cross-link to the
SKILL workflow section.

### 4. CLAUDE.md snippet (for projects not using the plugin)

The engine v4 plan ships a copy-paste CLAUDE.md snippet (its step 8). Keep the
plugin's version in sync: the session-start `status()` call, the bump-in-same-edit
rule, the first-add on-ramp, the three warning exits, and the decision table
condensed. This is the portable floor for un-plugged projects.

## FAQ section (keep it - reframed from the seven trust concerns)

Add a short FAQ to SKILL.md (or reference.md if SKILL grows too long). Each entry is
one of the standalone trust concerns turned into an agent-facing question with the v4
answer. This is the fastest lookup an agent has when it hits a symptom mid-task.

- **A run said "0 ran" - can I trust it?** Depends on intent. On an untouched
  pipeline, yes - that is the cache-trusted signal. Right after you bumped/reset a
  task, no - `ran=0` means the invalidation did not reach the cache; treat it as a
  bug. Check `result.ran` / `events.runs()` for the reason.
- **I edited code and nothing reran - why?** Cache identity is params + code_version,
  not code. If the task has no `code_version`, or you did not bump it, the stale
  output is reused. Bump it (and check `events.status()` for a pending warning naming
  the changed file).
- **The change was in a helper, not the task's `run()` - is that caught?** The
  advisory hash is transitive over repo-local imports, so editing `utils/foo.py`
  warns on every task that imports it. But the FIX is still per-task: bump each
  affected task's `code_version` (or reset). Missed ones keep warning in `status()`.
- **Which do I use - reset, bump, or accept_code?** See the decision table.
  One-liner: value -> Parameter; changed logic -> bump; identical-output refactor ->
  accept_code (only if certain); input data or corrupt cache -> reset.
- **Is `accept_code` safe?** It is the one exit that does NOT recompute - it blesses
  existing output as still valid. Wrong here = silent stale output. Use it only when
  you are certain the change is byte-identical in output; when unsure, bump (recompute
  is cheap insurance).
- **I changed a raw data file / the API returns new data - will it pick that up?**
  No - external input contents are a hash blind spot (no fingerprint moves). `reset()`
  the loader/source task that ingests it; the cascade recomputes downstream. Reset at
  the ingestion point, not downstream (downstream reload = cached old input).
- **The numbers changed and I do not know why.** `events.runs(task_family='X',
  last=2)` and diff params / code_version / source_hashes between the two runs.
- **What did the last session do? / did I already run X for Houston?**
  `events.status()` for the summary; `events.runs(task_family=..., ...)` for detail;
  the `flow` field answers per-metro "did this backtest run".
- **Can I trust a cached result at face value?** Only as far as the fingerprint sees:
  code + code_version + deps are covered; data-file contents, external APIs, and
  dynamic dispatch are not. For those, freshness is your responsibility (the reset
  rows), and the advisory will not claim otherwise (it is designed against false
  green).

## What to delete / supersede (do not silently leave contradictions)

- The per-param-variant `runLoad(reset=True)` workaround (~L605-618): replace with
  "a `code_version` bump invalidates all variants at once". Keep `runLoad(reset=True)`
  documented only as a targeted one-off recompute, not the standard fix for code
  edits.
- "keep reset lines as commented toggles in run.py" (~L288-290, L585-589): narrow to
  the reset-only cases (input data / corrupt cache); code edits are a bump, not a
  toggle.
- Any wording that implies a cache hit proves freshness: qualify with the blind-spot
  honesty.

## Backward compatibility

Keep both paths documented, clearly labeled. A task WITHOUT `code_version` behaves
exactly as today (edit -> reset -> run, no warning net) - say so, and recommend
adopting `code_version` (edit-free first pass) to get the net. Never tell an agent a
warning will catch a forgotten reset on a task that has not adopted the feature.

## Critical files
- Edit: `skills/oryxflow/SKILL.md` (main rewrite - workflow section, decision table,
  FAQ, RunResult update, supersede the reset-centric prose).
- Edit: `skills/oryxflow/reference.md` (API surface + advisory-honesty note).
- Edit: `skills/oryxflow/conventions.md` (scalars-as-memory motivation).
- Edit/sync: the copy-paste CLAUDE.md snippet (match engine v4 step 8).
- `docs/CHANGELOG.md`: entry noting the v4 alignment; `.claude-plugin/plugin.json`
  version bump when this ships.

## Verification
1. Grep the rewritten files for the old reset-only framing ("ONLY reset path" in the
   code-change sense, `runLoad(reset=True)` per-variant) - confirm each is superseded,
   not left contradicting the bump workflow.
2. Read-through as an agent hitting each symptom: every FAQ question resolves to a
   concrete call or table row; the decision table covers every verb.
3. Confirm the backward-compat path is explicit (no-code_version tasks) and no
   sentence implies the warning protects an un-adopted task.
4. ASCII-only (plugin convention); ~78-col wrap consistent with the other skill files.
5. Cross-check every API name against the engine v4 plan (events.status/runs,
   accept_code, keep_versions, RunResult.reasons/warnings/run_id, MultiRunResult
   aggregates) so the instructions do not reference a surface the engine does not ship.

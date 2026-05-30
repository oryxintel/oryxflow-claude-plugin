# Design notes - why the d6tflow skill is shaped this way

Rationale behind non-obvious decisions, so future edits do not undo them by
accident. Update this when the *reasoning* changes, not just the text.

## Two-tier content: SKILL.md vs reference.md

`SKILL.md` loads into context every time the skill activates; `reference.md` does
not. So `SKILL.md` carries only the essentials an agent needs on every task, and
everything deep (task-type tables, advanced patterns, recipes, the full
project-structure walkthrough) lives in `reference.md`, pulled in on demand.

Keeping `SKILL.md` lean is a recurring cost decision: every line is paid for on
each activation. Resist moving reference material up into it.

## The skill orients from per-project docs, not by re-scanning

A d6tflow data project is expected to keep `docs/claude-project.md` (pipeline:
tasks, deps, params) and `docs/claude-data-doc.md` (data: schema, quirks, rules).
These are the skill's **session cache**. On activation the skill reads them and
trusts them, instead of re-deriving project structure by scanning every file
each session.

Why: without this, every session re-explored the whole project (reading all
`.py`, listing `data/`, etc.) to rediscover what was already known. The docs turn
that one-time discovery into a durable artifact.

Implication: keeping those docs current is part of "done" for any change. A
change that does not update them makes the next session pay the scan cost again.

## Default invocation is lightweight; deep exploration is opt-in

A plain activation orients cheaply (read docs if present; otherwise classify the
project) and then stops. It does NOT auto-inspect `data/`, read raw sources,
write `eda/` scripts, or build the docs.

Why: that exploration is expensive and is the user's call to start. It runs only
on `/d6tflow explore` or a plain-language request to orient/explore/inspect. The
trigger surface is documented in `SKILL.md` so it stays discoverable.

## PLACEHOLDER SCAFFOLD marker - and the .py vs docs asymmetry

Scaffold `.py` files ship present and runnable (you cannot `from flow import
flow` from nothing, and the wiring is the thing worth demonstrating). To stop a
present file from being mistaken for real work, the placeholder LOGIC carries a
marker comment directly above it: `# PLACEHOLDER SCAFFOLD - ...`. The marker sits
on the task/params, not above the imports, because the imports are real code.

Docs are the opposite: they are NOT pre-created. Their *absence* is the signal
"nothing captured yet -> explore." A present-but-empty doc would defeat that
check (the agent would read structure and assume the project is documented).

So: file presence carries an unambiguous signal in both cases, but the signals
are inverted - `.py` present+marked = scaffold, docs absent = not captured.

## Fresh-scaffold report is onboarding, not a description of the guts

When classifying a fresh scaffold, the obvious move - "report the state" - leads
the agent to describe the placeholder logic it just read (dummy `range(10)`,
"Process doubles it"). That is a leak: those internals are throwaway wiring, not
project facts, and narrating them reads as if the project does something real.

So the lightweight report is split by state. A built pipeline gets summarized; a
fresh scaffold gets *onboarding* - a short welcome plus how to create tasks, load
data, and run the flow, then the two opt-in next steps. The placeholder guts are
explicitly off-limits to narrate. Keep this distinction if the report text is
ever reworked: the scaffold case is about getting the user started, not about
faithfully reporting what the scaffold contains.

## data/ holds two different things

Raw source inputs are typically loose files directly under `data/` (`.csv`,
`.xlsx`, etc.). d6tflow task OUTPUTS are parquet written into per-task subfolders
(`data/GetData/*.parquet`). When hunting for inputs, ignore the parquet
subfolders. The source path can be redirected via `cfg.py`.

## Open question - the two shipped "generic" docs

The minimal template repo (`d6tflow-template-minimal`) ships
`docs/claude-project.md` and `docs/claude-data-doc.md` that are NOT empty - they
are a rich template-usage guide and a detailed fill-in data-doc skeleton.

This collides with the "docs absence = explore" signal: those paths are the
per-project cache, but the shipped files are generic, not project-specific. They
contain genuinely useful content, so deleting them is not obviously right.

Unresolved: decide whether these are (a) templates a new project copies from
(kept out of the live cache paths, e.g. as `*.template.md` or folded into the
skill), or (b) the actual starting docs (then use a PLACEHOLDER-style banner
instead of relying on absence). Not yet decided; revisit before finalizing the
template repo.

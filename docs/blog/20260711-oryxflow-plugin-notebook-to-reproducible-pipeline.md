# Turning a notebook into a reproducible pipeline that only re-runs what changed

*2026-07-11*

At some point most data analysis outgrows the notebook it started in. The
notebook still produces the result, but it runs top to bottom, a small edit
re-executes everything, and a number you reported last month is hard to
regenerate now that the data has moved on. The usual next search is some version
of "how do I turn this into a reproducible pipeline" - and it is a well-trodden
path, with a whole shelf of tools built for it. This post is about what that step
actually requires, where oryxflow fits among the alternatives, and the one extra
thing it buys you if an AI agent is doing the work.

---

## What "reproducible pipeline" actually requires

Strip away the tooling and the goal has three concrete parts. Any solution worth
adopting has to deliver all three:

1. **The computation is defined by code, not by a session.** The steps and their
   order are declared explicitly, so "how was this produced" is answered by the
   pipeline, not by remembering which cells ran in what order. Re-running it
   gives the same result.

2. **Only what changed re-runs.** Editing one step should recompute that step and
   what depends on it - not re-read the source and redo everything upstream that
   did not change. Without this, "reproducible" is technically true but too slow
   to actually use while iterating, so people stop re-running and drift back to
   the notebook.

3. **Outputs are durable and reloadable.** Each step's result is saved in a form
   you can open later and check, rather than living in memory or scrollback. This
   is what lets a result be reproduced, audited, and reused downstream.

The first gives you reproducibility; the second makes it practical; the third
makes it checkable. A tool that gives you one or two of these but not all three
tends not to stick.

---

## Where oryxflow fits

oryxflow delivers the three directly. Steps are tasks with declared dependencies,
so the pipeline is the definition of the computation. A task's identity is its
code plus its parameters, so editing a step and resetting it recomputes only that
step and its dependents while everything unchanged stays cached. Outputs are
saved as typed artifacts you reload by asking for the task that produced them. In
other words, the three requirements above are the design, not add-ons.

Two things it adds beyond the baseline are worth calling out because they are
where iterative analysis actually spends its time:

- **Parameters instead of edited copies.** Because a parameter is part of a
  task's identity, running the same step under different settings - two models,
  two feature transforms, two date ranges - produces separate cached results that
  coexist. Comparing variants becomes running them, not copy-pasting blocks and
  hand-tracking which produced which. The parameters are the ledger.

- **A reset rule that is checkable.** Editing code does not change a task's
  identity on its own, so an edited-but-unreset task will quietly reuse its old
  output. This is the one sharp edge of any cache-based system, and oryxflow makes
  it explicit: reset the edited task before re-running, and confirm from the run
  result which tasks actually recomputed. It turns the classic "did my change
  even take effect" doubt into a one-line check.

---

## An honest look at the alternatives

oryxflow is not the only way to get a reproducible, incrementally-recomputed
pipeline, and it is worth being straight about where the others are strong. The
right choice depends on what your work looks like.

- **joblib.Memory** caches individual function results with a decorator. It is
  the lightest possible option and great for memoizing an expensive load or
  transform inside otherwise-normal code. What it does not give you is a
  dependency graph or a project structure - it is a cache, not a pipeline, so it
  solves requirement 2 in the small but leaves 1 and 3 to you.

- **DVC** is excellent when the hard part is versioning large data and model
  files alongside git, and it does incremental stage re-runs well. It is heavier
  to set up, git- and file-centric, and oriented toward tracking artifacts across
  commits. If your central problem is "my datasets and model binaries are huge
  and I need them versioned and shareable," DVC may fit better than a
  code-first task library.

- **R's `targets`** is a genuinely great pipeline tool with the same
  only-run-what-changed model - if you work in R. It is not a fit for a Python
  codebase.

- **Snakemake / Nextflow** are rule- and file-based workflow engines, strong for
  batch and scientific-computing pipelines and heavier orchestration. They lean
  toward files-as-the-interface and an ops flavor, which is powerful but more
  than an analyst iterating on a model in Python usually wants.

oryxflow's spot in that landscape: Python-native, the pipeline expressed as tasks
in code rather than config or a separate DSL, parameter identity for comparing
variants, and light enough to adopt inside an ordinary analysis project. It aims
at the person iterating on the analysis itself, not at large-file versioning or
cluster orchestration. If your problem is the former, it fits; if it is squarely
the latter, one of the others may serve you better, and that is a fine answer.

---

## The part specific to working with an AI agent

There is one more reason to define the pipeline as tasks in code, and it has
become more relevant as more of this work is done through an AI coding agent.

A pipeline whose steps and dependencies are declared explicitly is not just
reproducible for you - it is legible to the agent. It can reconstruct what feeds
what from the declarations without reading every line, orient in a project it has
not seen, and know what an edit invalidated instead of guessing. The same
structure that makes the computation reproducible is what keeps an agent from
losing the thread on a project with more than a handful of steps. And the durable,
reloadable outputs are what let the agent - or you - check a reported number
against the actual saved result rather than taking a summary on faith.

That is the throughline: the properties that make a pipeline reproducible are the
same ones that make it safe for an agent to work in. You are not choosing between
"reproducible for humans" and "workable for AI"; they are the same requirements.

---

## The honest boundary

For a genuinely one-off analysis, none of this is worth it - write the notebook,
get the answer, move on. The reproducible-pipeline step earns its keep when the
work is something you iterate on, come back to, and have to be able to regenerate:
enough steps that re-running everything hurts, enough variants that comparing them
by hand is bookkeeping, and enough stakes that a number you cannot reproduce is a
real problem. That is exactly the point at which the notebook stops being enough,
and it is the point oryxflow is built for.

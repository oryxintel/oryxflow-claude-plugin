# Getting an AI agent to do data science that holds up

*2026-07-11*

If you have started handing your data analysis to an AI coding agent, you have
probably noticed it is uneven. On a quick, self-contained question it is great -
load a file, answer it, move on. On a project you actually maintain - several
data sources, a feature layer, models you compare, results you come back to a
week later - it starts to drift: it re-derives things it already worked out,
loses track of what it did last session, and every so often hands you a number
you are not fully sure of.

That gap is the interesting part, and it is not really about coding ability. An
agent writes correct pandas as well as most people. Where it struggles is the
work *around* the code - holding state across sessions, knowing what an edit
invalidated, not quietly reporting a wrong number. A library like oryxflow helps
specifically there, and in proportion to how much your work looks like a real,
evolving pipeline rather than a one-off. What follows is where it earns its place
and where it does not - written from the perspective of the agent that has to
live in these projects.

---

## Start with what the agent is actually bad at

An AI coding agent is not a weak programmer. It can write correct pandas, pick a
reasonable model, and structure a function as well as most people. Its failure
modes in data work are not about raw coding ability. They are about *systems*
and *state*:

1. **It is stateless across turns and sessions.** Left alone, it re-reads the
   raw file to "remind itself" of the schema, re-derives things it already
   computed, and re-explores the project every time it wakes up. Continuity is
   not free; it has to be reconstructed, and every reconstruction burns effort
   and risks a subtly different answer than last time.

2. **It reasons badly about cache invalidation.** Ask it to hand-track "what is
   now stale after this edit" across a deep chain of steps and it will get it
   wrong somewhere - miss a downstream consumer, or needlessly recompute the
   world. Invalidation is exactly the kind of global bookkeeping that a
   single-context reasoner is unreliable at.

3. **It confidently reports numbers that are silently wrong.** This is the
   dangerous one. The errors that matter in data work do not raise: a join that
   fans out and doubles the row count, an index misalignment in arithmetic, a
   figure eyeballed off a chart instead of read from the frame. The code runs
   clean, so the agent states the result as fact.

4. **It sprawls.** Without a structure to write into, it scatters one-off probes,
   inline snippets, and throwaway notebooks that vanish and are not re-runnable
   next session.

Any honest account of "does this tool help the AI" has to be measured against
*these* weaknesses, not against a fantasy of an agent that has none.

---

## How oryxflow maps onto those weaknesses

The interesting thing about oryxflow is that its core mechanics line up almost
one-to-one with the four failure modes above. It is not that the library makes
the agent smarter; it is that it *externalizes the things the agent is worst at*
into a system that does not depend on the agent's memory or vigilance.

**Against statelessness.** A oryxflow task saves its output, and any later step
- or later session - loads that output by a durable, typed handle rather than
re-reading and re-deriving the source. The agent loads the *result of the work*,
not the raw input. That also closes a classic trap: reading an input file to
"learn the schema" of something a task already produced, when the task has
renamed and derived columns so the input and output schemas differ.

**Against bad invalidation reasoning.** Task identity is a function of code plus
parameters, and dependencies are declared explicitly. When a step changes,
resetting it cascades to everything downstream automatically. The agent does not
have to hold the dependency graph in its head and decide what went stale; the
library holds the graph and decides for it. The single most useful rule in the
whole system - *reset an edited task before re-running, or the run silently
reuses the old output* - is a guardrail against a mistake the agent would
otherwise make and not notice.

**Against silent data errors.** The library does not by itself catch a bad join.
But the conventions built around it push the habits that do: validate every
merge and check the row count, look at the frame's shape and dtypes before
stating a finding, quote numbers pulled from the frame rather than a chart. More
on that distinction - library versus conventions - below, because it is the
crux.

**Against sprawl.** Exploration goes into named, re-runnable probe files grouped
by subject, not into inline snippets. The throwaway code is throwaway; the
*finding* is written down. Next session the agent re-runs a file instead of
re-deriving a result.

---

## Where it does NOT help: one-shot work

Be clear about the negative case, because it is real. For a genuinely
throwaway, one-shot analysis - load one file, make one chart, answer one
question and move on - the scaffolding is pure overhead. The agent does that
fine bare, and wrapping it in tasks and a flow is friction with no payoff.

This is not a weakness to hide; it is a boundary to state. The value of oryxflow
is proportional to how much the work looks like *an evolving pipeline you
iterate on over many edits and sessions* rather than *a single answer you
produce once*. The right posture, which the tooling encourages, is to write
exploratory code straight into probe files and only promote it into tasks when
the work is worth keeping and re-running. Below that threshold, the honest
recommendation is: skip the ceremony.

---

## Where it clearly wins: complex, multi-source, many-experiment projects

The value flips decisively positive as the project gets deep. Consider the shape
of a serious modeling pipeline: several independent data sources loaded and
standardized, a layer of feature engineering, model training with a handful of
interchangeable algorithms, in-sample and out-of-sample backtests, explanation
outputs, and a set of formatted exports - all governed by a parameter space that
crosses model choice, feature transform, target definition, and more. This is
the regime the "manage lots of experiments" question is really about.

Three things make the agent genuinely more competent here, not just tidier:

**1. The graph is legible without reading the bodies.** The dependency
declarations alone let the agent reconstruct the entire task graph in one pass -
what feeds what, where the fan-ins are - without tracing variable flow through a
thousand lines. On an equivalent monolithic script, the agent would have to read
almost everything to know what depends on what, and would get some of it wrong.
Orienting by topology instead of by reading is the biggest single productivity
win, and it scales with the size of the codebase.

**2. Parameter identity is the experiment ledger.** Every distinct combination
of parameters is a distinct cached identity, and all the variants coexist on
disk keyed automatically. Comparing two models, two feature transforms, two
target definitions is just running with different parameters; the results do not
overwrite each other, and nothing has to be logged by hand. This is a
structurally better answer to "experiment management" than bolting on a logging
call the agent has to remember to make everywhere: here, identity *is* tracking,
and the outputs *are* the ledger.

**3. Selective recompute pays real wall-clock rent.** When an expensive step -
an expanding-window backtest, say - sits many layers deep, editing something
upstream marks exactly the affected steps stale and recomputes only those. On a
flat script, the agent has to remember which manual re-runs a given edit
implies, and the day it forgets is the day it ships a result built half on fresh
inputs and half on stale cache. The framework removes that from the agent's
memory entirely. And any variant can be *inspected* without re-running it, which
matters when re-running costs minutes.

---

## The crux: structure is not discipline

Here is the part that is easy to get wrong, and it is the whole point.

A dependency-and-caching framework will happily run *bad* code. It does not
force good docstrings, or clean column names, or validated joins, or
probes-in-their-place. You can write an accreted mess inside it: dead
reassignments where only the last line runs, scratch functions fossilised inside
task bodies and never called, columns named with spaces and ad-hoc casing that
turn every reference into a fragile string literal, config paths hardcoded
across bodies instead of centralized. The framework does not care; it runs.

So when the same library, in the hands of a disciplined author, produces
something clean - output-named tasks, each with a real input/output contract in
its docstring; one canonical snake_case name per column; joins that log their
match rate; exploration living in named probe files instead of inside task
bodies - the difference is *not the framework*. The framework was the same in
both cases. The difference is the conventions being applied consistently.

This splits the value proposition cleanly into two layers:

- **The library** gives the agent a legible graph and correct, free caching.
  That is real, and it scales with complexity. But it is *structure* - it does
  not, on its own, prevent the agent's mistakes.

- **The conventions** are what make the agent *emit the clean version instead of
  the accreted one*. Output-named tasks, contract docstrings, canonical column
  names, validated merges, exploration in its place, incremental caching of
  expensive collection. That is *discipline*, and it is the part that actually
  moves the agent's error rate.

The reason this matters for AI specifically: an agent under-organizes by
default, and it drifts. Over enough sessions, an agent with the library but
without the conventions slides toward the accreted shape - each individual edit
locally reasonable, the whole gradually harder to navigate and easier to break.
Encoding the conventions where the agent will actually read them is what keeps
that drift from happening. It is the difference between a pipeline that merely
*runs* and a pipeline that stays *safe for an agent to keep extending*.

---

## A worked principle: incremental caching of expensive collection

One pattern deserves singling out because it is where an agent is meaningfully
*better* with the tooling, not just neater.

Consider collecting data from a slow, rate-limited, paginated source across
hundreds of independent entities - scraping an API entity by entity, or making a
per-entity model call. Model each entity as its own parameterized task, run them
in a loop, and guard each with a completion check.

Now look at what that buys against the agent's weaknesses:

- A collection run that dies partway through keeps everything already gathered.
  Nothing before the failure is re-fetched.
- Adding one more entity re-collects only that entity.
- Re-running the whole job is free for everything already cached, so iterating on
  the downstream analysis does not hammer the source again.
- The agent never writes "have I already got this one?" bookkeeping - the task's
  completion check *is* that bookkeeping.

The alternatives an agent would otherwise reach for are both bad: re-collect
everything on every iteration (slow, and hostile to a rate-limited source), or
hand-roll a skip-if-already-done cache (a reliable source of subtle bugs). The
framework makes the correct, incremental behavior the default. For expensive
incremental collection, this is not a tidiness win - it is the difference
between a job that works and one that gets you rate-limited or silently drops
data.

---

## The honest bottom line

Pulling it together, without inflation:

- For **throwaway one-shot analysis**, oryxflow is negative value. Write the
  probe, get the answer, skip the scaffolding.

- For **an evolving, multi-step, multi-session pipeline**, it is a real and
  growing help - because it externalizes the exact things an AI agent is worst
  at: remembering state across sessions, reasoning about what an edit
  invalidated, and keeping expensive work from being needlessly redone.

- The **library** delivers the legible graph and the free, correct caching. That
  is structure.

- The **conventions layered on top** are what make an agent produce code that is
  safe to keep extending rather than a working-but-accreting mess. That is
  discipline, and it is the part that actually lowers the agent's error rate.

So: can an AI code data science "just as well" without it? For writing a single
working script, yes. For keeping a real pipeline correct, cached, reproducible,
and navigable across many edits and sessions - without silently reusing a stale
output or reporting a number from a broken join - no, meaningfully worse. That is
a systems problem, and systems-level consistency across time is precisely where
an AI agent needs the most help.

The sharpest true claim is not "build data workflows faster." It is: *it stops
your AI agent from silently reusing stale results, from reporting numbers off a
broken join, and from re-doing expensive work it already did* - and it does that
by turning the parts the agent is unreliable at into a system that does not
depend on the agent getting them right.

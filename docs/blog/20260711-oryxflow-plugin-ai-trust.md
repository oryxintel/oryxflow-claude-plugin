# Can you trust an AI's data analysis?

*2026-07-11*

It is a fair thing to ask before acting on a number an AI handed you, and the
honest answer is: not on faith. Not because the agent is a weak programmer - it
writes correct pandas as well as most people - but because of how mistakes behave
in this kind of work. They usually do not announce themselves.

In ordinary programming a wrong result tends to surface on its own - the code
throws, a test fails, the page does not render. In data work it often does not. A
join can quietly change the number of rows, an arithmetic step can misalign two
indexes, a percentage can be computed against the wrong denominator, and the
pipeline still runs to completion and prints a number. The number is wrong and
nothing says so. Add that the agent works from a single pass with no memory of
last session and cannot see a mistake that raised no error, and taking its
analysis on trust is clearly the wrong default.

So the useful question is not "is the agent trustworthy" but "can its work be
checked without re-deriving it by hand?" That is where a library like oryxflow
fits: less as a correctness guarantee, more as the thing that makes the work
reproducible and inspectable so checking is cheap. This is written from the point
of view of the agent doing the work - what tends to go wrong, and where the
library and its conventions help, and where they do not.

---

## What tends to go wrong

A few failure modes come up repeatedly. None are exotic.

**Silent data errors.** The main one. A merge that should be many-to-one is
actually many-to-many and inflates every downstream aggregate. An operation
across two misaligned indexes. A figure read off a chart by eye and typed into a
summary rather than pulled from the data. All of these complete without error and
produce a plausible result.

**Reusing stale output after an edit.** In an iterative workflow this is easy to
miss. A task's identity is its code plus its parameters, so editing the *code*
does not change its identity - and a plain re-run will treat the task as already
done and reuse the previous output. The run looks successful; the number is from
before the edit. Unless you check, nothing distinguishes it from a real
recomputation.

**Results you cannot reproduce.** If an analysis was assembled from inline
snippets and one-off commands over a session, it produced its number once. Asked
for that same number later - after the source refreshed, or after a small change -
there may be no reliable way to regenerate it, because the exact sequence was
never recorded anywhere durable.

**State that is not written down.** Ad-hoc scripts carry implicit state: what was
in memory, which of several assigned paths actually ran, what order cells were
executed in. When the result depends on things that were never captured, it
cannot be audited and does not survive the session.

The common thread is that all of these are hard to catch from the output alone.
The output looks the same whether the computation underneath was right or wrong.

---

## Where the library and conventions help

The honest framing is that oryxflow does not make the analysis correct. What it
does is make results reproducible and inspectable, and the conventions layered on
top push the specific habits that catch the silent errors. Mapped to the failure
modes above:

**Reproducibility comes from the structure itself.** Each step is a named task
with declared dependencies, and the pipeline re-runs deterministically. There is
no separate description of "how this was produced" that can drift from reality -
the code is that description, and running it again gives the same result. Any
output can be re-opened later by loading the task that produced it. That directly
addresses the "cannot reproduce" and "undocumented state" cases: the record is
the pipeline, not the agent's memory of a session.

**You can tell what actually re-ran.** The reset-before-re-run rule is the
guardrail for stale output, and it is checkable: the run returns a result object
that reports which tasks recomputed versus which were cache hits. "The run did not
error" is not evidence that an edit took effect; "this task shows as having
re-run" is. It is worth being clear that this is a discipline the agent has to
follow, not something the library does automatically - but the tool to confirm it
exists, and using it turns an easy-to-miss failure into a one-line check.

**The silent-error checks are conventions, not library behavior.** The library
will not catch a fan-out join. The conventions are what make the agent check:
validate the join and assert the row relationship, look at the frame's shape,
dtypes, and nulls before stating a finding, quote numbers pulled from the saved
frame rather than eyeballed from a chart. These are ordinary practices; the value
is that they are written where the agent will apply them as it works, so they
shape the analysis rather than being a review checklist someone runs afterward.

**Results live as artifacts you can open.** A number that will be read more than
once belongs in a saved table, not scraped from console output. Because outputs
are persisted as typed artifacts, a claim in the write-up can be checked against
the thing it describes - you open the same frame the agent summarized and see
whether it holds - instead of taking the summary's word for it.

---

## Library versus conventions

It is worth separating the two, because they do different jobs and the
distinction is honest about what you get from what.

The **library** gives you the substrate: reproducible task identity, a
deterministic dependency graph, durable typed outputs, a run result you can
interrogate. These are what make verification possible in the first place.
Without them, checking the agent's analysis means rebuilding it by hand.

But the library will run unchecked work as readily as checked work. It does not
require a join to be validated or a finding to be recorded. On its own it gives
you a pipeline that *could* be audited, not one that *was*.

The **conventions** supply the habits that do the checking, delivered where the
agent reads them so they apply during the work. Neither half is sufficient alone:
the library makes analysis checkable, the conventions make it checked. If there
is a single reason the plugin exists on top of the library, this is it.

---

## What this does not do

To be clear about the boundaries: none of this makes the agent's *judgment*
trustworthy. The library reduces the mechanical, silent-error class of problems
and makes everything reproducible and inspectable. It does not tell you whether
the model is appropriate, whether the methodology is sound, or whether an analysis
that runs cleanly is answering the right question. A computation can be perfectly
reproducible and still conceptually wrong, and a human still has to look at the
substance. What changes is that looking is now cheap - you can re-open any result,
confirm what actually ran, and re-derive the conclusion - rather than requiring
you to reconstruct the work before you can even begin to check it.

And for genuinely throwaway, one-shot analysis, the structure is overhead. Its
value shows up when the work is something you iterate on and come back to, where
reproducibility and the ability to check a prior result actually matter.

---

## In short

You should not take an AI's data analysis on faith. In this domain the failure is
usually not a crash but a confident wrong number, produced as fluently as a right
one, from a mistake that raised no error. The realistic response is not to hope
the agent is careful, but to keep the work on a footing where results are
reproducible, executions are checkable, and the common silent errors are caught
by habit. oryxflow provides that footing; its conventions provide the habits.
Together they do not make the agent trustworthy - they make its work cheap to
verify, which is the more useful thing.

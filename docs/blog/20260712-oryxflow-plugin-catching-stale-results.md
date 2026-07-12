# Catching the stale result an AI agent would otherwise ship

*2026-07-12*

An earlier post here argued that you should not take an AI's data analysis on
faith, and that the useful response is to keep the work reproducible and cheap to
check. In listing where the library helped, it made one honest admission: the rule
that guards against reusing stale output after an edit - reset the task before you
re-run it - was *a discipline the agent has to follow, not something the library
does automatically*. The tool to confirm a reset took existed; remembering to do it
was on the agent.

That admission was the weak point, and it is the one worth fixing, because it sits
on the single most dangerous failure mode in the whole list. This post is about
what changes when the library stops trusting the agent's memory for it - written,
like the others, from the point of view of the agent doing the work - and an honest
accounting of how much of the trust gap it actually closes.

---

## The failure, restated

The dangerous error in data work is not a crash. It is a confident wrong number,
produced as fluently as a right one, from a mistake that raised no error. Stale
cache is the purest example. A task's cached identity is its parameters, not its
code, so editing the code does not change its identity - and a plain re-run treats
the task as already done and reuses the old output. The run reports success. The
number is from before the edit. Nothing distinguishes it from a real
recomputation.

Two things make this worse for an AI agent specifically. First, the edit that
matters is often not in the task at all - it is in a helper function or a shared
constant the task calls, so the task body is byte-for-byte unchanged while its
behavior is completely different. Any "did this task change" instinct that looks
only at the task is fooled. Second, the remedy was an act of memory: remember,
after every edit, to reset the right task. An agent's recall degrades across a long
session, and a correctness guarantee that routes through "the agent remembers to do
X" fails some fraction of the time. Rules that must be recalled get missed.

So the honest state of things was: the library made the mistake *recoverable and
checkable*, but it did not *catch* it. Catching it was on the agent, and the agent
is exactly the part you cannot fully rely on to catch it.

---

## What changes: the system does the invalidation

Three things move the stale-result problem off the agent's memory and into the
system.

**Editing code just reruns it - no bump, no reset.** By default the library
fingerprints each task's code *and the project files it imports, transitively*,
normalized so that comments and formatting changes are invisible and never cry
wolf. Change a task's logic and, on the next run, that task and everything
downstream of it recompute on their own - the whole edit-then-remember-to-reset
dance is gone, and so is the earlier remedy of bumping a version by hand. It also
catches the case that fooled the old "did this task change" instinct: the edit that
hid in a helper in `utils/`, leaving the task body byte-for-byte identical, moves
the fingerprint just the same, because the fingerprint follows the imports. And
because the code identity is not tied to any one parameter value, a single edit
invalidates *every* parameter variant at once - the old hazard where you reset the
variant you named and the other `env` or model variants stayed silently stale is
retired too. One safety valve rides along the automatic path: a task whose last run
was expensive - over a configurable threshold - does *not* silently recompute on a
code change. It warns and waits, so a refactor never quietly burns a long run; you
reset it, accept it, or pin it, on purpose.

**When you want manual control, you pin - and a warning guards it.** Automatic is
the right default, but not always the right sensitivity: a task you want recomputed
only on a deliberate call rather than on any refactor (the guard above already
spares the most expensive runs; a pin makes that control explicit and reaches tasks
below the threshold), logic the hash cannot see (dynamic dispatch, behavior driven
by a config file), or a headline task whose cache decision you want visible in
review and `git log`. Declare a
`code_version` on such a task and it opts out of automatic tracking: it recomputes
only when you bump the token, and if you edit it *without* bumping, the run warns -
naming the changed file - rather than quietly rerunning or serving stale output.
The warning offers three explicit exits: bump (a real change, recompute), accept (a
refactor that does not change the output, re-stamp it), or reset (recompute
regardless). Pinned and automatic tasks coexist in one pipeline, and a pinned task
still reruns when an automatic upstream changes - the pin holds only its own logic.

**A durable record of what ran, so the agent is not working from memory.** Every run
appends to an event log: what ran, with which parameters and version, why it ran
(missing output, code change, upstream rerun), how long it took, what failed. An
agent starting a fresh session asks the log one question - what is pending, what ran
last, what failed - instead of guessing or grepping old console output. "The numbers
changed and I do not know why" becomes a diff of the last two runs' parameters and
code versions. And the scalars a task already logs while it runs - a correlation, a
drop rate, a row count - are captured into that log, so the sanity checks the agent
made mid-analysis become next session's memory instead of vanishing with the
terminal. The cross-session amnesia that made an agent re-derive and re-explore is
answered by a record, not by the agent's recall.

---

## The honest accounting

None of this makes the agent's memory unnecessary, and it is worth being precise
about what it does and does not remove - the same honesty the prior posts insisted
on.

**Automatic does not mean unattended - the job is now to verify.** The action moved,
it did not vanish. Instead of remembering to invalidate an edited task, the agent's
job is to *confirm the invalidation landed*: after an edit you expect to recompute,
the next run must show the affected tasks as having re-run, with a reason that names
the code change. A run that reports zero tasks re-ran after you just edited code is
the tell that something is wrong - not a convenient cache hit. That is a check, not
a feat of memory, and a check is exactly the kind of mechanical thing that is cheap
to make a habit.

**The fingerprint has blind spots, and it says so.** It sees code and the code a
task imports. It does not see the contents of a data file the task reads, a value
returned by an external API, or a helper reached by dynamic dispatch. When one of
those changes, nothing moves the fingerprint and the edited task does *not* rerun -
which is exactly what the verify habit above catches: the zero-ran surprise is the
signal that the change is in a blind spot, and the fix is to reset the task that
reads the changed input yourself. The design's response to its own limits is
deliberate: where it cannot be sure, it stays quiet rather than asserting "up to
date", because a false green is worse than an honest silence - a cache hit is never
proof of freshness for what the hash cannot see.

**One of the three exits can still bite.** Bump and reset both recompute, so they
are safe by default. "Accept" - marking a change as output-equivalent - does not
recompute; it blesses the existing output as still valid. Used on a change that
actually did shift the numbers, it re-stamps a stale result with no rerun and no
further warning. It is the one exit that trusts the agent's judgment, and the honest
guidance is to reach for it only when you are certain the output is identical, and
to bump when you are not.

**It does not touch judgment.** As before: a computation can be perfectly versioned,
fully reproducible, and conceptually wrong. Whether the model is appropriate,
whether the methodology is sound, whether a clean-running analysis answers the right
question - none of that is in scope. What is now cheaper is everything mechanical
underneath it.

---

## Which lever, when

The one real cost of adding pins, accepts, and resets to a workflow that already had
parameters is a moment of "which do I reach for". It resolves to a short rule:

- Changed a **value or knob** that is a parameter - do nothing; a new parameter is a
  new identity and reruns on its own, keeping the old result beside it.
- Changed the **logic** of a task or a helper it imports - do nothing; it and
  everything downstream rerun on their own, across all its variants. Then verify
  the rerun landed.
- Want a task to recompute **only on a deliberate call** - an expensive step, or
  logic the hash cannot see - pin it with a `code_version` and bump that when you
  mean it.
- Changed code but the **output is provably identical** (a rename, an extracted
  function, an added log line) - accept it, to skip the rerun it would otherwise do,
  but only if you are sure; when unsure, let it recompute.
- The **input data changed** (a raw file refreshed, an API returned new numbers) -
  reset the task that reads it; the fingerprint cannot see this, so it is on you.
- Something looks **corrupt, or you just want it gone** - reset.

The failure the old world could not name cleanly was the input-data case, and it is
still the one that stays on the agent's shoulders. The rest are now the system's job.

---

## What actually changed about trust

The prior post's thesis was that the library does not make the agent trustworthy; it
makes the agent's work *cheap to verify*. That is still true, and it is still the
right frame. What this adds is narrower and worth stating exactly: the most common
silent error - shipping a number computed by code you already changed - is now
*prevented by default*, because the edited code simply reruns, including when the
change hid in a helper; and where the change is something the hash cannot see, the
run's own record turns the miss into a visible zero-ran surprise rather than a
silent success. The record of what ran *survives the session* instead of living in
the agent's fading memory of it.

That is not "trust the agent now". It is: the specific mistake you were most right to
worry about no longer depends on the agent remembering not to make it - it happens on
its own - and the agent's remaining job shrinks to a check, confirming the rerun
landed. For the class of work these tools are for - an evolving pipeline you edit and
return to over many sessions - that is the difference between a result you have to
re-derive before you can believe it and one that tells you, on its own, whether it is
current.

The judgment is still yours to check. The stale number is not, anymore, the one that
gets past you.

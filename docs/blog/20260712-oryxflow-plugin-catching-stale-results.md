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

## What changes: the system catches the forgetting

Three things move the stale-result problem off the agent's memory and into the
system.

**A version you bump instead of a reset you remember.** Each task can carry a
`code_version`. When you change the task's logic, you bump it, in the same edit that
changed the code - and the bump propagates downstream automatically, recomputing the
edited task and everything that depends on it. One idiom replaces the old
edit-then-remember-to-reset dance. It also quietly retires an old trap: because the
version is part of the task's code identity and not tied to any one parameter value,
a single bump invalidates *every* parameter variant of that task at once. The old
hazard - reset the variant you named, and the other `env` or model variants stay
silently stale - is gone.

**A warning when you forget to bump - including the helper case.** Bumping is still
an act of memory, so the system watches for the forgetting. It fingerprints the
task's code *and the project files it imports, transitively*, normalized so that
comments and formatting changes are invisible and never cry wolf. Edit a helper in
`utils/` that a task depends on, forget to bump, and the next run warns - naming the
file that changed - rather than silently serving the stale output. The warning fires
at the moment of the decision, on a channel you see by default, and it offers three
explicit exits: bump (this was a real change, recompute), accept (a refactor that
does not change the output, re-stamp it), or reset (recompute regardless). This is
the crux of the whole change: the check fires where the mistake happens, instead of
being a rule the agent had to carry.

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

**The warning is a net, not a guarantee.** Bumping the version is still the primary
action, and it is still something the agent has to do. What changed is that
forgetting is now *caught* rather than *silent* - a recoverable miss instead of a
shipped wrong number. That is a large improvement and it is not the same as
eliminating the mistake.

**The fingerprint has blind spots, and it says so.** It sees code and the code a
task imports. It does not see the contents of a data file the task reads, a value
returned by an external API, or a helper reached by dynamic dispatch. When one of
those changes, no version moves and no warning fires - a cache hit is not proof of
freshness there. The design's response is deliberate: where it cannot be sure, it
stays quiet rather than asserting "up to date", because a false green is worse than
an honest silence. But that means a real category remains the agent's
responsibility - when you know the input data changed, you still have to force the
recompute yourself, at the task that reads it.

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

The one real cost of adding versions, accepts, and resets to a workflow that already
had parameters is a moment of "which do I reach for". It resolves to a short rule:

- Changed a **value or knob** that is a parameter - do nothing; a new parameter is a
  new identity and reruns on its own, keeping the old result beside it.
- Changed the **logic** of a task or a helper it imports - bump its `code_version`;
  the rerun propagates downstream and across all its variants.
- Changed code but the **output is provably identical** (a rename, an extracted
  function, an added log line) - accept it, but only if you are sure; when unsure,
  bump.
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
*caught at the moment it would happen*, including when the change hid in a helper,
and the record of what ran *survives the session* instead of living in the agent's
fading memory of it.

That is not "trust the agent now". It is: the specific mistake you were most right to
worry about no longer depends on the agent remembering not to make it, and when the
agent does forget, the system says so instead of staying quiet. For the class of work
these tools are for - an evolving pipeline you edit and return to over many sessions -
that is the difference between a result you have to re-derive before you can believe
it and one that tells you, on its own, whether it is current.

The judgment is still yours to check. The stale number is not, anymore, the one that
gets past you.

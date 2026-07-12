# Stop re-running your whole pipeline to change one step

*2026-07-11*

Here is a frustration anyone doing data analysis knows. You change one feature,
and to see its effect your script re-reads the file, re-cleans it, and retrains -
redoing a pile of work that did not change just to test a one-line edit. Then you
want to compare two models, so you edit the call in place and lose the first
result. Then the metric you liked scrolls off the screen and you are no longer
sure which version produced it.

None of that is a bug. It is just what a flat script does, and an AI agent working
the same way inherits all of it. The fix is not more care in the script; it is
giving the steps enough structure that only what changed recomputes, variants
coexist instead of overwriting each other, and results are saved rather than
printed. That is what a pipeline library like oryxflow provides.

The re-run tax is only the part you notice first, though, and it is the least of
it. It costs you time, not correctness. The same structure quietly prevents the
failures that actually carry a cost: reasoning over a stale result after an edit
and never realizing it, shipping a number a silent join error corrupted, or
landing on a figure you cannot reproduce next week. In fact the stale-result case
is the flip side of the very caching that saves the time - the mechanism that
skips unchanged work is, if you do not reset an edited step, exactly what serves
you an old number as if it were new. Speed is the visible benefit; not being
wrong is the one that matters. The clearest way to see how the structure delivers
both is to run the same small workflow two ways - once the way an agent does it by
default, once as a oryxflow pipeline - and then look at what happens as the
project grows.

Take a familiar workflow: load a table, clean it, build some features, train a
model, and report a metric.

---

## Without: one script, re-run top to bottom

Done bare, this tends to become a single script (or notebook) that runs start to
finish each time:

```python
# analysis.py
df = pd.read_csv("data/raw.csv")
df = clean(df)
df = add_features(df)
model, metric = train_and_eval(df)
print("rmse:", metric)
```

For the first pass this is fine. The friction shows up on the second, third, and
thirtieth pass - which is where data work actually lives.

- **Every run redoes everything.** Tweaking `add_features` re-reads the file and
  re-runs `clean` too, even though neither changed. When one of those steps is
  slow, each iteration pays for work that did not change.
- **Comparing options means editing in place.** To try a second model you swap
  the call, or copy the block, or comment-toggle. The two results do not
  coexist; the second overwrites the first, and keeping both means bookkeeping
  you do by hand.
- **The number lives in scrollback.** The metric you liked was printed once.
  Three iterations later it has scrolled away, and reproducing it means
  remembering exactly which version of the code produced it.
- **State is implicit.** Which file was actually read, what was in memory, what
  order things ran in - none of it is written down. Next session the agent
  reconstructs it, sometimes slightly differently.

None of this is catastrophic on a five-line script. It is a slow, low-grade tax,
and it is exactly the kind of tax that compounds.

---

## With: the same steps as tasks

The same workflow as a oryxflow pipeline is the same logic, cut along the same
seams, but each step is a task with declared inputs:

```python
# tasks.py
class DataRaw(oryxflow.tasks.TaskPqPandas):
    """Raw table as loaded from source."""
    def run(self):
        self.save(pd.read_csv("data/raw.csv"))

@oryxflow.requires(DataRaw)
class DataClean(oryxflow.tasks.TaskPqPandas):
    """Typed, de-duplicated rows; nulls handled."""
    def run(self):
        self.save(clean(self.inputLoad()))

@oryxflow.requires(DataClean)
class Features(oryxflow.tasks.TaskPqPandas):
    """Model-ready feature matrix + target."""
    def run(self):
        self.save(add_features(self.inputLoad()))

@oryxflow.requires(Features)
class ModelFit(oryxflow.tasks.TaskPickle):
    """Trained model + in-sample metric for `model`."""
    model = oryxflow.Parameter()
    def run(self):
        m, metric = train_and_eval(self.inputLoad(), self.model)
        self.save(m); self.saveMeta({"rmse": metric})
```

The same four iterations look different:

- **Only what changed recomputes.** Edit `Features`, reset it, re-run - `DataRaw`
  and `DataClean` are cache hits; `Features` and `ModelFit` recompute. The slow
  upstream steps are paid for once.
- **Comparing options is a parameter, not an edit.** Running `ModelFit` with
  `model="rf"` and with `model="gbm"` produces two cached results that coexist,
  each keyed by its parameter. Nothing is overwritten and nothing is tracked by
  hand - the parameter is the label.
- **The number is a saved artifact.** The metric is stored on the task, not
  printed into scrollback. Any later step, or a later session, loads it with
  `flow.outputLoad(...)` and gets the same value.
- **State is explicit.** The dependencies are declared, the steps are named, and
  the pipeline re-runs deterministically. "How was this produced" is answered by
  the code, not by memory of a session.

There is a cost: four task classes instead of five lines. On a workflow this
small, that overhead is close to a wash - honestly stated, if this were the whole
project you could skip the structure and not lose much. The reason to reach for
it is what happens when the project stops being small.

One caveat worth keeping honest: the recompute-only-what-changed behavior depends
on resetting an edited task before re-running, since editing code does not change
a task's identity on its own. That is a habit, not something the framework does
for you - but it is a checkable one, and it is the hinge the rest turns on.

---

## The tease: what this looks like when the project is real

Now scale the same shape up to the kind of project these tools are actually for.
Not one dataset but several, loaded and standardized separately. Not one feature
step but a layer of engineered features with their own transforms. Not one model
but a handful of interchangeable ones, each compared across several parameter
settings. An expensive evaluation deep in the graph - an out-of-sample backtest
that retrains as it walks forward. Maybe a slow, rate-limited collection step
that gathers data entity by entity. And a dozen downstream outputs: tables,
exports, a report.

Re-read the "without" list against that project and each line stops being a
low-grade tax and becomes a real problem:

- "Every run redoes everything" now means re-running an expensive backtest, or
  re-hitting a rate-limited source, every time you touch anything upstream of it.
- "Comparing options means editing in place" now means managing a grid of
  model-by-transform-by-target combinations by hand, with results that overwrite
  each other and no reliable ledger of which run produced which number.
- "The number lives in scrollback" now means a headline metric you cannot
  reliably reproduce next week after the data refreshed.
- "State is implicit" now means a thousand-line script where, among other things,
  a path gets assigned three times and only the last line runs - and neither you
  nor the agent can easily tell.

The "with" story, by contrast, does not change shape as the project grows - it
just has more nodes:

- The dependency graph stays legible. An agent can reconstruct what feeds what
  from the declarations alone, without reading every step - which is the
  difference between orienting in a project it has never seen and getting lost in
  it.
- Each parameter combination is its own cached identity, so comparing a grid of
  variants is running them, not bookkeeping them; the results coexist and the
  parameters are the ledger.
- The expensive backtest and the slow collection step run once per distinct
  input and are reused after. A collection that dies partway keeps what it
  gathered; adding one entity re-collects only that one.
- Every output is an artifact you can re-open and check against the claim made
  about it, and the whole pipeline reproduces the result rather than relying on a
  remembered session.

That is the real return. The small example shows the mechanics; the value is that
those mechanics hold flat while the project's complexity - and the cost of the
"without" failure modes - grows underneath them.

---

## The honest summary

For a genuinely small, one-off analysis, doing it bare is fine and the pipeline
structure is overhead you can skip. The moment the work becomes something you
iterate on - more steps, slow steps, variants to compare, results to reproduce -
the same four frictions that were a mild tax on the toy example turn into the
things that actually slow a project down and let wrong or stale numbers through.
oryxflow's job is to keep those from scaling with the project: recompute only what
changed, let parameters stand in for hand-managed experiments, and make every
result reproducible and inspectable. On the small example that is a convenience.
On the real one it is what keeps the project tractable.

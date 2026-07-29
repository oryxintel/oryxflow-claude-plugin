# Structuring a DAG that fans out (loops, grids, per-item work)

Loaded on demand when the work is shaped like a LOOP: "for each region / model /
file", a parameter grid, a per-X-then-combine hierarchy, or a migration source
full of `for` statements. Needs `oryxflow >= 26.7.28` for `@oryxflow.requires_each`
and stacked dependency decorators; the `requires_grid` method form needs the same.

The one idea: when the shape of the work comes from a LIST, declare the list once
and let oryxflow generate one task per item. You do NOT hand-write the branches,
and you do NOT loop inside `run()`.

## Decide first: what KIND of loop is it

Classify before you write anything. Most mistakes here are picking the wrong row.

| What you see | What it is | Build it as |
|---|---|---|
| Loop over a fixed list, results combined | fan-out + combine | `@oryxflow.requires_each(Dep, x=cfg.LIST)` on the combining task |
| Loop over a list computed from THIS task's params | dynamic fan-out | `requires_each(Dep, x=lambda self: ...)`, or `self.requires_grid` in `requires()` |
| Nested loops, inner list INDEXED BY the outer value (`for country: for state in STATES[country]:`) | hierarchy | one aggregator task per level (below) |
| Nested loops over INDEPENDENT knobs (`for sector: for horizon:`) | grid, NOT a hierarchy | ONE `requires_each(Dep, sector=S, horizon=H)` - cartesian product |
| Loop over variants you manage SEPARATELY (own run, own reset) | independent runs | `WorkflowMulti` (reference.md Pattern 1) |
| Loop INSIDE one step's computation (rows, columns, a fit's folds) | not a DAG shape | a plain `for` in `run()` - leave it alone |

**The fan-out threshold**: fan out when each branch is worth CACHING on its own -
it is slow, hits the network, or you want to reset just it. Do NOT fan out cheap
per-item work: `for row in df.iterrows()` is not 10,000 tasks, it is one task with
a loop in it. Ask "would I ever want to re-run just this branch?" If no, keep the
loop.

**The same list in 2+ tasks is an AXIS, not a loop.** `for sec in ['Apartment',
'Office', ...]` repeated across tasks means the whole pipeline is sector-wise: make
`sector` a Parameter and fan out, even where one task's loop is cheap enough to
keep on its own. The REPETITION is the cost - copies of the literal drift apart,
nothing can be run or reset for one sector, and every task added later inherits the
loop. This outranks the threshold above: a fan-out is justified by one slow branch,
and equally by an axis the pipeline shares.

## The default: `@oryxflow.requires_each`

One dependency per value, and a combining task that stacks them:

```python
# cfg.py -- the enumeration is YOUR domain data, plain config, not a oryxflow object
REGIONS = ['north', 'south', 'east']

class RegionLoad(oryxflow.tasks.TaskPqPandas):
    region = oryxflow.Parameter()

    def run(self):
        self.save(fetch_raw(self.region))

@oryxflow.requires_each(RegionLoad, region=cfg.REGIONS)
class RegionCombine(oryxflow.tasks.TaskPqPandas):
    """All regions in one frame, tagged by region."""

    def run(self):
        self.save(self.inputLoadConcat())   # stacks branches, adds a `region` column
```

What the decorator does - it replaces BOTH jobs `@oryxflow.requires` does:

- declares one dependency per value (no `requires()` method needed);
- copies the dependency's parameters onto the combining task **minus the fanned-out
  ones**. That is what turns the fan-out back into a single node - it is the one
  place the branches meet, so everything downstream goes back to plain
  `@oryxflow.requires` and never learns that N branches existed.

`self.inputLoadConcat()` stacks the branch outputs and tags each row with that
branch's parameters, so `df.groupby('region')` works immediately. Adjust with
`tagkeys=[...]` (tag only these), `tag=False`, or `concat_fn=` (full control).

Add a value to `cfg.REGIONS` and only the new branch runs; the rest are cached.

### A setting that follows from the fanned value: `derive=`

When each branch needs a second thing determined by its value - a per-region source file, a
per-model tuning dict, a per-market threshold - do NOT look it up in the branch's `run()`.
Derive it, so it becomes a parameter of the branch:

```python
SOURCE = {'north': 'north-2026.csv', 'south': 'south-2026.csv'}

@oryxflow.requires_each(RegionLoad, region=list(cfg.SOURCE),
                        derive={'source': lambda v: cfg.SOURCE[v['region']]})
class RegionCombine(oryxflow.tasks.TaskPqPandas):
    def run(self):
        self.save(self.inputLoadConcat())
```

The callable takes the branch's fanned **values dict** (`v['region']`; `v['model']` and
`v['horizon']` with two fanned parameters), never `self`, and must be a deterministic lookup or
calculation on them. `RegionLoad` must declare `source = oryxflow.Parameter()` - a derived name
with no matching parameter RAISES rather than being dropped.

Why it matters: the derived value lands in the branch's `task_id`, so editing
`cfg.SOURCE['south']` invalidates south alone. The same lookup written as
`read(cfg.SOURCE[self.region])` inside `run()` is invisible to the cache - the branch's stored
output does not know which file it came from, so a changed mapping returns the OLD output with no
warning. `code_version` is not the fix; it reruns every branch.

Do not fan out over the lookup (`region=REGIONS, source=SOURCE.values()`) - `requires_grid` takes
the cartesian product, so that is N^2 branches.

Derived names stay out of the dependency keys (`inputLoad(task='north')` unchanged) and off the
combining task, exactly like fanned names.

### The cost of looping inside `run()` instead

You get the same numbers from a `for` loop that builds a sub-`Workflow` per item.
Do NOT - the cost lands on the NEXT change, not this one. Tasks started inside a
`run()` are not dependencies, so nothing can find them:

- `flow.reset_upstream(RegionCombine, only=RegionLoad)` invalidates nothing and
  reports no error. You change how a region loads, reset "just that step", re-run,
  and get the OLD numbers back - green run, no warning.
- `flow.preview()` cannot show the branches; the run summary does not count them.
- A branch failure does not name which branch.

Declared as a fan-out, every reset reaches every branch, preview counts them
before you start, and a failure names its parameters
(`RegionLoad(region=south): ValueError: ...`).

## Hierarchy: iterate, then aggregate, level by level

Nested loops become one aggregator task per level. Each level's `run()` is just
`self.inputLoadConcat()`; the level's own parameters carry DOWN to its branches
without being listed.

```python
# cfg.py
UNIVERSE = {'Retail': {'US': ['CT', 'NY']}, 'Office': {'US': ['CA']}}

class Country(oryxflow.tasks.TaskPqPandas):
    sector = oryxflow.Parameter()
    country = oryxflow.Parameter()

    def requires(self):        # list computed from this task's own params -> requires_grid
        return self.requires_grid(ProcessState,
                                  state=cfg.UNIVERSE[self.sector][self.country])

    def run(self):
        self.save(self.inputLoadConcat())

@oryxflow.requires_each(Country, country=lambda self: list(cfg.UNIVERSE[self.sector]))
class Sector(oryxflow.tasks.TaskPqPandas):
    sector = oryxflow.Parameter()

    def run(self):
        self.save(self.inputLoadConcat())
```

Because the whole hierarchy is ONE DAG, `preview()` shows every leaf, the run
summary lists them, and `flow.reset_upstream(Sector, only=DataLoadState)`
enumerates every leaf instance across the tree - no hand-tracking.

Each level re-tags the columns the level below already carries, with the same
values - an idempotent overwrite, not double-counting.

Name the enumeration for what it HOLDS (`STATES`, `UNIVERSE`), never `grid` - that
invites confusion with the unrelated `WorkflowMulti` params.

## Fan-out vs `WorkflowMulti` (the top-level choice)

Both run N variants. They differ in what you get back:

- **Fan-out** (one more aggregator on top) - ONE flow, one combined output, one
  reset scope, one run summary. Default choice when you want the variants
  compared in a single frame.
- **`WorkflowMulti`** - N separate flows, each with its own run summary,
  `outputLoad`, and reset scope. Choose it when the variants are separately
  MANAGED experiments (prod tiers, A/B runs you reset independently).

Same result frame either way; pick by how you want to manage them, not by shape.

## Combining a fan-out with a shared input

A combining task usually needs something the branches do not have - the table they
were built from, a benchmark to score against, labels to render with. Stack the
decorators (any order, any number):

```python
@oryxflow.requires({'input': ReportInput})                     # shared, NOT fanned out
@oryxflow.requires_each(RegionNarrative, region=cfg.REGIONS)   # the fan-out
class Report(oryxflow.tasks.TaskMarkdown):

    def run(self):
        deps = self.inputLoad(flatten=False)
        drivers = deps['input']
        for region, narrative in deps['RegionNarrative'].items():
            ...
```

- `inputLoad(flatten=False)` groups the branches under ONE key (the dependency's
  task name), so you never pop the inputs you recognise and assume the rest are
  branches. `inputLoad(task='RegionNarrative')` /
  `inputLoadConcat(task='RegionNarrative')` select just the branches.
- Two fan-outs that would produce the same keys: name one -
  `@oryxflow.requires_each({'chart': RegionChart}, region=cfg.REGIONS)`. Colliding
  keys RAISE rather than one quietly replacing the other.
- Keep an expensive branch's input OUT of the branch when it is shared: fold a
  drivers table into each LLM-call narrative and re-formatting it re-bills every
  region.

## When the list is not known until the data is read

The DAG is built before anything loads, so you cannot ask the data which items
qualify. Fan out over the FULL list and let empty branches say so:

```python
class RegionModel(oryxflow.tasks.TaskPqPandas):
    region = oryxflow.Parameter()

    def run(self):
        df = self.inputLoad()
        if len(df) < cfg.MIN_ROWS:
            self.save(pd.DataFrame())      # nothing here -- cheap, and cached
            return
        self.save(fit(df))
```

An empty branch costs nothing and caches like any other; `inputLoadConcat()`
ignores it. In exchange the workflow stays VISIBLE - preview lists every region
including the ones that produced nothing, and a region that starts qualifying
later is a re-run, not a code change.

A callable grid value sees the task's **parameters**, not its inputs - it is
evaluated while the DAG is assembled. `run()` can `yield` tasks as a last resort,
but they are created mid-run, so `preview()` cannot show them and a targeted reset
cannot find them.

## Migrating a source full of `for` loops

Working through a notebook or script (see `/oryxflow:migrate` step 2), classify
EACH loop against the table at the top before porting it. In order:

1. **Does the loop body produce a cacheable artifact per item?** No (it builds up
   one frame row by row, fits one model's folds) -> it stays a plain loop inside
   one task. Stop here. Yes -> you are SPLITTING one task into two, not decorating
   the task that exists: the loop BODY becomes a new task whose Parameters are the
   loop variables, and the task that held the loop becomes the combining task. A
   body that is already one helper call (`fit_sector(df, sec, h)`) makes this
   mechanical - that call is the new task's whole `run()`.
2. **Where does the list come from?** A literal / config constant -> `cfg.py`, then
   `requires_each`. Computed from a parameter of the task -> a callable or
   `requires_grid`. A directory listing (`glob.glob('data-raw/*.csv')`) -> also
   `requires_each`; each file caches separately, so a new file re-reads only itself.
3. **Nested loops** -> one aggregator per level, outermost last. Do not flatten a
   two-level loop into one fan-out over tuples; you lose the intermediate cache.
4. **Is the accumulator a `pd.concat` at the end?** That is the combining task's
   entire `run()`: `self.save(self.inputLoadConcat())`. Drop the list-append.
5. **Loops that write intermediate files** (`to_csv(f'clean_{x}.csv')`, later read
   back) -> that is the branch's `self.save()`; the file goes away.

Do not port a loop that built a `Workflow` per item - that is the anti-pattern
above, and migration is the moment to remove it. But before you convert one:

6. **Check where the nested flow was WRITING.** A task's outputs live under its
   flow's directory, and the inner `oryxflow.Workflow(...)` usually had different
   `path`/`env` settings from the outer one - most often none at all, so it wrote
   to the default `data/` while the outer flow runs under `data/env=<env>/`.
   Convert without checking and the branches are looked for where they were never
   written: the cache reads as empty and every item re-runs. Nothing warns,
   because "no output at that path" is indistinguishable from "never ran" - and on
   an LLM or paid-API fan-out that silence costs real money. Report the directory
   delta to the user and let them choose: move the existing outputs under the
   outer flow's directory, or accept a knowing one-off recompute. Say the reverse
   out loud too - a nested flow with no `env=` was sharing one set of outputs
   across every environment, which is its own bug; the recompute is the cost of
   un-sharing them.

## Gotchas

- **Never declare the fanned-out parameter on the combining task.** `TypeError` at
  class definition. It would put one branch's value in the combining task's
  identity - one combining task per value, each combining all branches, at N times
  the cost. The combining task is where branches converge; it must not carry the
  parameter they differ on.
- **A task cannot have both a hand-written `requires()` and a dependency
  decorator** - `TypeError`. Keep one: drop the decorator and use
  `self.requires_grid(...)` inside `requires()`, or delete the method.
- **A per-branch lookup inside `run()` is invisible to the cache** - use `derive=` (above) so it
  reaches the branch's identity. This is the fan-out bug that costs money quietly: change the
  mapping, re-run, get the old outputs, no warning.
- **The fanned-out and derived names must be parameters of the dependency** - `TypeError` naming
  the ones it does have. Fanning out over a name it lacks used to give N keys pointing at ONE
  task, so `inputLoadConcat()` returned N copies of one output tagged as separate branches.
- **`derive`, `cls`, `path` and `flows` cannot be parameter names** - `ValueError` at class
  definition (`derive`/`cls` are `requires_grid()`/`clone()` arguments; the engine owns
  `path`/`flows`). Use `derive_features`, `model_cls`, `file`.
- **Branch keys** are the value itself for one parameter (`'ridge'`), or
  `name_value` pairs joined with `_` for several (`'horizon_5_model_ridge'`). Those
  keys are what `inputLoad(task=...)` selects on.
- **`inputLoadConcat()` warns** when it would row-stack a shared dependency in with
  the branches (a union frame across unrelated schemas). Pass `task='<group>'`, or
  `flatten=False` for one frame per group.
- **The enumeration is plain domain data.** Keep it in `cfg.py`, not in a task, not
  in `flow_params.py` - the fan-out reads it when the tasks are DEFINED, so editing
  it and re-running your script picks up the change.
- **Shared upstream stays shared.** A dependency without the fanned parameter is
  ONE task no matter how many branches ask for it - a data load feeding five model
  variants runs once. If it is re-running per branch, it has picked up the
  parameter somewhere.

## Where else to look

- `reference.md` - `WorkflowMulti` (Pattern 1), the load/save cheat-sheet,
  `reset_upstream` / `reset_downstream` semantics.
- `ml-patterns.md` - the model-variant comparison and prod orchestration built on
  this.
- Library docs: https://docs.oryxflow.dev/docs/advtasksdyn/index.md (the full
  mechanics reference) and `.../docs/managing-workflows/index.md` (why and when).

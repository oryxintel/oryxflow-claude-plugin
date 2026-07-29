# oryxflow Reference: Working with oryxflow Workflows

Comprehensive LIBRARY reference loaded on demand by the `oryxflow` skill. Covers
core concepts in depth, task types, working with tasks, running workflows,
advanced patterns, best practices, avoiding silent data errors, data-science
recipes, and debugging. For the HOUSE conventions - project layout, grouping
supporting code, and naming columns / tasks / variables - see
[conventions.md](conventions.md).

## What is oryxflow?

**oryxflow** is a Python library for building highly effective data science
workflows. It lets you chain together complex, parameterized data flows and
execute them, caching intermediate calculations so you build better models
faster.

### Key Benefits
- **Dependency management**: Automatically runs tasks in the correct order
- **Caching**: Only re-runs tasks when inputs change
- **Parameter tracking**: Different parameters create different task instances
- **Data persistence**: Automatically saves/loads data between tasks
- **Reproducibility**: Complete lineage of data transformations

### When to Use oryxflow
- Multi-step data pipelines (loading -> cleaning -> features -> models -> predictions)
- Machine learning workflows with dependencies between tasks
- Workflows that need to be re-run with different parameters
- Projects where you want automatic caching and incremental computation

---

## Core Concepts

### 1. Tasks

Building blocks: Inherit from oryxflow task class, have `run()` method, save
outputs automatically, uniquely identified by class name + parameters.

**Naming**: name a task for the OUTPUT it produces (a noun: `OEWSWages`,
`CleanedSales`, `TrainedModel`, `DataOEWS`), not the verb it performs; avoid
generic names like `GetData` / `LoadData` / `Process`; order tokens broad ->
narrow so a family clusters (`FundamentalsLeadLag`, not `LeadLagAnalysis`). Full
rules in [conventions.md](conventions.md) ("Task naming"). Some examples below use
older verb-style names for brevity; prefer output names in real code. The class
examples omit `code_version` by design: auto invalidation (oryxflow >= 26.7.12,
on by default) reruns an edited task on its own, so `code_version` is an opt-in
LOCK you add only to pin an expensive or hash-blind task (see "Code edits vs
parameter changes" below).

```python
import oryxflow
import pandas as pd

class LoadData(oryxflow.tasks.TaskPqPandas):
    """Load raw data from CSV"""
    def run(self):
        df = pd.read_csv('data.csv')
        self.save(df)  # Auto-saves as parquet
```

### 2. Task Types

| Task Type | Output Format | Use Case |
|-----------|---------------|----------|
| `TaskPqPandas` | Parquet | DataFrames (default choice, fast) |
| `TaskCSVPandas` | CSV | Last resort - only a reader you cannot change (below) |
| `TaskExcelPandas` | Excel | DataFrames a HUMAN opens (reports) |
| `TaskPickle` | Pickle | Any Python object (models, dicts, lists) |
| `TaskJson` | JSON | Dictionaries, simple data structures |
| `TaskMarkdown` | Markdown (+ HTML) | Narrative text a task GENERATES (an LLM write-up, a rendered section) |
| `TaskAggregator` | None | Groups tasks declared in `requires()` (empty `run()`), saves no output |

**Format rule - this is a ranking, not a menu of equals**: `TaskPqPandas` for
every DataFrame, `TaskPickle` for models/objects. Drop to CSV/Excel ONLY when a
HUMAN opens the file (`TaskExcelPandas`) or a system you CANNOT change reads it.
A downstream repo YOU own is not such a system - it changes its reader (one
line); the pipeline does not change its format.

CSV carries no dtypes, and the cost lands in the CONSUMER, not the writer:
numeric-looking string keys (ZIP / account codes) round-trip to ints and
lose leading zeros or gain a `.0`, and dates come back as strings needing a
`format=` guess - which is how a consumer ends up branching on the FILENAME to
pick a date format. If you have written repair code for a mangled CSV INPUT, do
not emit a CSV OUTPUT: same bug class, re-introduced one hop downstream.

Reproducing a legacy CSV artifact does NOT make CSV the requirement - the
contract is its SCHEMA (the named columns), not its container. An export
convention inherited from a decade-old tool is a convention, not a spec.

### 3. Dependencies

Declare with `@oryxflow.requires()` decorator. Auto-runs tasks in correct order.

```python
@oryxflow.requires(LoadData)
class CleanData(oryxflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()  # Load from LoadData
        self.save(df.dropna())

# Multiple dependencies
@oryxflow.requires(LoadData, LoadMetadata)
class MergeData(oryxflow.tasks.TaskPqPandas):
    def run(self):
        df_data, df_meta = self.inputLoad()
        self.save(df_data.merge(df_meta, on='id'))
```

**One dependency PER ITEM of a list** (oryxflow >= 26.7.28):
`@oryxflow.requires_each(Dep, param=values)` declares a branch per value and copies
`Dep`'s parameters onto the decorated task MINUS the fanned-out ones, so the
combining task is the single node the branches converge into.
`Task.requires_grid(cls, **grid)` is the same thing written inside your own
`requires()`, for when the list comes from the task's own parameters. Decorators
STACK (`@oryxflow.requires` + `@oryxflow.requires_each`, any order, any number) so a
combining task can also take a shared, not-fanned-out input. Full decision table,
hierarchies, and gotchas: [dynamic-dags.md](dynamic-dags.md).

BREAKING (26.7.28): the free function `oryxflow.utils.requires_grid(cls, param,
values, **base)` is now the `Task.requires_grid(cls, **grid)` METHOD. With no
`self` it could not carry the calling task's parameters down to the branches -
every shared parameter had to be repeated in `base`, and one left out was silently
missing from the children (they got the DEFAULT - a wrong result, not an error).
`requires_grid(ModelTrain, 'model', MODELS)` becomes
`self.requires_grid(ModelTrain, model=MODELS)` inside `requires()`, and anything
you passed via `base` can be deleted.

Two errors this raises at class definition, both previously silent:

- A hand-written `requires()` **plus** a dependency decorator -> `TypeError`. The
  decorator assigns `requires` after the class body, so the method used to be
  discarded silently. Keep one.
- A task decorated `@oryxflow.requires_each(Dep, x=[...])` that also declares
  `x = oryxflow.Parameter(...)` -> `TypeError`. The declaration used to survive and
  put one branch's value into the combining task's identity - one combining task
  per value, each combining all branches, at N times the cost. Delete the
  declaration.

Two dependencies resolving to the same key now raise `ValueError` from `requires()`
instead of one silently replacing the other; name one of them
(`@oryxflow.requires_each({'chart': Chart}, region=REGIONS)`).

### 4. Parameters

Parameters make tasks dynamic and reusable. They affect task identity:

```python
class ProcessData(oryxflow.tasks.TaskPqPandas):
    date = oryxflow.DateParameter()
    region = oryxflow.Parameter()
    threshold = oryxflow.IntParameter(default=100)

    def run(self):
        df = self.input().load()
        df = df[df['region'] == self.region]
        df = df[df['value'] > self.threshold]
        self.save(df)
```

**Parameter Types**:
- `oryxflow.Parameter()` - String
- `oryxflow.IntParameter()` - Integer
- `oryxflow.FloatParameter()` - Float
- `oryxflow.BoolParameter()` - Boolean
- `oryxflow.DateParameter()` - Date
- `oryxflow.ListParameter()` - List
- `oryxflow.DictParameter()` - Dictionary
- `oryxflow.ChoiceParameter(choices=['rf','lgbm'], default='rf')` - string
  restricted to a fixed set; an off-list value raises at task construction
  (fail-fast on typos), NOT deep in downstream code. Values stay plain strings,
  so it drops into existing string-valued params with zero churn - prefer this
  for categoricals like `model='rf'`.
- `oryxflow.EnumParameter(enum=MyEnum)` - value is an `enum.Enum` member (pass the
  enum class). Same fail-fast benefit but heavier: you define an `enum.Enum` and
  rewrite values from `'rf'` to `MyEnum.rf`. Use only when you genuinely want
  enum objects; for plain string choices, `ChoiceParameter` is lighter.

**Important**: Same class + same parameters = same task instance (cached).
Different parameters = different task instance (separate cache).

**Reserved names**: `path`, `flows`, `cls` and `derive` cannot be Parameter names -
each raises `ValueError` at class definition (oryxflow >= 26.7.28). They are
arguments the engine owns: `path` = the flow's DATA DIRECTORY, `flows` = flows
attached with `attach_flow()`, `cls` / `derive` = arguments of `clone()` /
`requires_grid()`. A Parameter of that name binds to the ARGUMENT instead, so
`MyTask(path='a.csv')` never reached it - the Parameter kept its DEFAULT, mapping
every value to the same task, and that default then became the output directory
(`x.csv/MyTask/...`). Rename: `file` / `filename`, `model_cls`,
`derive_features`. This bites hardest in a per-file fan-out, where `path` is the
tempting name.

### 5. Parameter Inheritance

Parameters auto-inherit from dependencies. Use `significant=False` for params
that do not affect task identity:

```python
class TaskA(oryxflow.tasks.TaskPqPandas):
    date = oryxflow.DateParameter()
    verbose = oryxflow.BoolParameter(default=False, significant=False)

@oryxflow.requires(TaskA)
class TaskB(oryxflow.tasks.TaskPqPandas):
    # Auto-inherits 'date' and 'verbose' from TaskA
    def run(self):
        df = self.inputLoad()
        # self.date available here
```

---

## Working with Tasks

### Load / save cheat-sheet

Pick the identifier by WHAT (data vs meta), WHERE (inside `run()` vs outside with
a `flow`), and HOW MANY (all vs one):

| What you want                | Inside `run()`                          | Outside (have `flow`)              |
|------------------------------|-----------------------------------------|------------------------------------|
| Declare N outputs            | `persists = ['a','b']` (class attr)     | -                                  |
| Save N outputs, list form    | `self.save([a, b], from_list=True)`     | -                                  |
| Save N outputs, dict form    | `self.save({'a': a, 'b': b})`           | -                                  |
| Save metadata                | `self.saveMeta({'model': m})`           | -                                  |
| Load ALL outputs             | `self.inputLoad()` -> tuple             | `flow.outputLoad(Task)`            |
| Load ONE output (by name)    | `self.inputLoad(keys='a')`              | `flow.outputLoad(Task, keys='a')`  |
| Pick ONE dependency          | `self.inputLoad(task='name')`           | -                                  |
| Load metadata                | `self.metaLoad(key=0)`                   | `flow.outputLoadMeta(Task)`        |
| Stack a fan-out's branches   | `self.inputLoadConcat()`                | -                                  |
| Group branches under one key | `self.inputLoad(flatten=False)`         | -                                  |

Notes:
- An OUTPUT is selected by name (`keys=`); a DEPENDENCY by name/index (`task=`,
  or `self.input()[i]` for positional `requires`). `[0]`/`[1]` NEVER picks an
  output.
- Lower-level "load one output": `self.input()['a'].load()` - index the persist
  NAME first, THEN `.load()`. `self.input().load(keys='a')` does NOT work for a
  multi-`persists` dep (`self.input()` is a dict, not a target).
- TRAP: `load()`/`inputLoad()` swallow unknown kwargs silently, so a wrong
  selector returns the whole/default output with NO error - e.g.
  `load(persist='a')` (the kwarg is `keys=`, not `persist=`).
- `inputLoadConcat()` (fan-out only) stacks the branch outputs and TAGS each row
  with that branch's parameters, so `groupby` works straight away; silence a tag
  with `tagkeys=[...]` / `tag=False`. It WARNS if it would row-stack a shared
  dependency in with the branches - pass `task='<group>'` for just the branches,
  or `flatten=False` for one frame per group. See
  [dynamic-dags.md](dynamic-dags.md).

### Loading Data from Upstream Tasks

Rule: prefer `self.inputLoad()` - it returns the DATA. `self.input()` returns the
raw Target (use it only for `.path` or a deliberate `.load()`). Select an output
with `keys=` (never `persist=` - that kwarg is silently ignored; see trap above).

```python
# Single dependency, single output
@oryxflow.requires(UpstreamTask)
class MyTask(oryxflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()

# Single dependency, multiple outputs (persists=['train','test'])
@oryxflow.requires(SplitData)
class MyTask(oryxflow.tasks.TaskPqPandas):
    def run(self):
        df_train, df_test = self.inputLoad()        # all outputs, in persists order
        df_train = self.inputLoad(keys='train')     # just one, by name
        df_train = self.input()['train'].load()     # lower-level equivalent

# Multiple dependencies - PREFER the named-dict form (select deps by name)
@oryxflow.requires({'data': LoadData, 'meta': LoadMetadata})
class MyTask(oryxflow.tasks.TaskPqPandas):
    def run(self):
        df_data = self.inputLoad(task='data')       # or self.input()['data'].load()
        df_meta = self.inputLoad(task='meta')

# Multiple dependencies, positional - select deps by INTEGER index
@oryxflow.requires(Task1, Task2, Task3)
class MyTask(oryxflow.tasks.TaskPqPandas):
    def run(self):
        df1, df2, df3 = self.inputLoad()
```

Selection rules - `self.input()` mirrors `requires()`:

- single dep, single output -> a Target -> `self.input().load()`
- single dep, multiple `persists` -> a `{name: target}` dict ->
  `self.input()['train'].load()`
- positional `requires(T0, T1)` -> a list -> `self.input()[0]` (and
  `self.input()[0]['train']` if T0 has multiple outputs)
- named `requires({'a': T0, 'b': T1})` -> a dict -> `self.input()['a']`

(For the by-name vs by-index rule and the silent-unknown-kwarg trap, see the
cheat-sheet above.)

### Saving Multiple Outputs

```python
class SplitData(oryxflow.tasks.TaskPqPandas):
    persists = ['train', 'test', 'valid']  # output names
    def run(self):
        df = self.inputLoad()
        # list -> saved positionally, in persists order; needs from_list=True
        self.save([df.sample(frac=0.7), df.sample(frac=0.2), df.sample(frac=0.1)], from_list=True)

# Loading
@oryxflow.requires(SplitData)
class TrainModel(oryxflow.tasks.TaskPickle):
    def run(self):
        df_train, df_test, df_valid = self.inputLoad()

# Dictionary outputs - same persists; dict keys select by name
class MyTask(oryxflow.tasks.TaskPqPandas):
    persists = ['data', 'metadata']
    def run(self):
        self.save({'data': df_main, 'metadata': df_meta})
```

`persists` names the outputs; `persist` (singular) is a backwards-compatible
alias for the same attribute. List-vs-dict is chosen by what you pass to
`save()`, not by the attribute name.

### Saving Metadata (Models, Configs)

For models and configs that do not fit standard formats:

```python
class TrainModel(oryxflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()
        model = RandomForestClassifier()
        model.fit(df[features], df['target'])
        df['pred'] = model.predict(df[features])
        self.save(df)
        self.saveMeta({'model': model, 'accuracy': 0.95, 'features': features})

# Loading metadata
@oryxflow.requires(TrainModel)
class ApplyModel(oryxflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()
        meta = self.metaLoad()
        df['pred'] = meta['model'].predict(df[meta['features']])
        self.save(df)

# Load from specific dependency (key=0 is first)
@oryxflow.requires(TrainModel, LoadData)
class MyTask(oryxflow.tasks.TaskPqPandas):
    def run(self):
        meta = self.metaLoad(key=0)  # From TrainModel
        df = self.input()[1].load()  # From LoadData
```

---

## Running Workflows

### Basic Execution

```python
# flow.py - Create workflow
flow = oryxflow.Workflow(FinalTask, params={'date': '2024-01-01'})

# run.py - Execute
result = flow.run()
print(result.summary())          # ran / cache-hit / failed; result.success/.ran/.failed to drill down
df = flow.outputLoad()

# Check status
flow.preview()   # Preview what will run
flow.complete()  # Returns True if all tasks complete
```

### Forcing Re-runs & Loading Outputs

```python
# Reset (force re-run) - flow.reset is the preferred path
flow.reset(TaskName)                      # ONE task's own output (no prompt by default)
flow.reset(TaskName, confirm=True)        # opt IN to a confirmation prompt
flow.reset_downstream(TaskName)           # that task + everything between it and the terminal
flow.reset_upstream(Anchor)               # Anchor + its whole upstream cone
flow.reset_upstream(Anchor, only=Family)  # just that FAMILY within the cone (every instance)
flow.resetAll()                           # entire workflow
flow.run([TaskName()], forced_all=True)   # force this task + its upstream
flow.run(forced_all_upstream=True)        # force everything

# Load outputs
result = flow.outputLoad()                # Final task
df = flow.outputLoad(IntermediateTask)    # Specific task
df_train = flow.outputLoad(SplitData, keys='train')  # Specific output by name
meta = flow.metaLoad(TrainModel)          # Metadata
```

**When to reset**: auto could not SEE the change (source DATA changed, dynamic
dispatch, a notebook-defined task), you suspect a corrupt cache, or you want
outputs deleted. When it is changed input data, reset at the LOADER task that
ingests it, not a downstream task - a downstream reset re-loads the cached old
input, so the change never propagates. For ordinary CODE edits you do NOT reset -
auto reruns them (below).

**`flow.reset` does NOT delete downstream outputs** - it invalidates ONE task
(`Workflow.reset` -> that task's `reset()`). Downstream recompute is INFERRED
later, when the build evaluates `complete()`, and the two mechanisms differ:

- **Auto ON (default)**: an upstream that actually rematerialized gets a new
  `output_id`, so every downstream record's folded dep state no longer matches and
  the band is incomplete regardless of walk order. A plain `flow.reset` is enough.
- **Auto OFF** (`settings.code_version_auto = False`, no `code_version` pins):
  there is no code identity anywhere in the chain, so that dimension goes INERT and
  the only propagation left is `settings.check_dependencies` - which the build
  evaluates LAZILY, per task, as it walks (a complete task is skipped WITHOUT
  descending into its deps). A branch reached BEFORE the reset task is rebuilt sees
  the missing output and reruns; a branch reached AFTER sees it restored and stays
  CACHED on stale input. Propagation is therefore partial and order-dependent.

`reset_upstream(Anchor, only=Family)` is the scoped form a FAN-OUT needs: it walks
the full upstream cone to DISCOVER every instance of `Family` (every region, every
`(sector, country)` pair) and invalidates only those, leaving the expensive
neighbours cached - no hand-listing. All three take an ANCHOR task; there is no
no-argument form on `Workflow`. This works only because the branches are real
`requires()` edges - it is precisely what a loop inside `run()` gives up (see
[dynamic-dags.md](dynamic-dags.md)).

So with auto off, to invalidate a BAND use `flow.reset_downstream(TaskName)`, which
deletes every complete task between it and the terminal. The terminal defaults to
the flow's default task - on a multi-final pipeline pass `task_downstream=` per
final, or branches that do not reach the default are silently missed.
(Verified against oryxflow 26.7.21: `Workflow.reset`, `TaskData.complete`,
`TaskData._code_ok`, `core.build._process`.)

**Code edits vs parameter changes (the iterate gotcha, mostly gone)**: oryxflow
caches by task identity = class + parameters. A PARAMETER change creates a new
identity, so it reruns on the next `flow.run()`. A CODE edit (a task's `run()`
body, a helper it calls, or a module-level CONSTANT it reads) does NOT change
identity - but auto invalidation
(oryxflow >= 26.7.12, `settings.code_version_auto = True` by default) hashes the
task's own class plus the project-local symbols it transitively references -
helpers, constants, and project-local base classes alike, per SYMBOL not per file
(AST-normalized: comment / docstring / formatting edits never count; editing an
UNRELATED sibling task or constant in the same file reruns nothing - one
monolithic `tasks.py` or a shared `cfg.py` stays cheap). A `cfg.py` edit reruns
exactly the tasks that read the edited symbol: reorder a concept list a task
consumes and it refetches; change an unrelated date constant and it does not.
So the edited task and everything downstream rerun on
the next run anyway, overwriting in place. So the old "reset before running an
edited task" ritual is gone; the new discipline is to VERIFY the rerun landed -
after an edit the task must appear in `result.ran` with reason
`code change (auto: <file>::<symbol>)`. If it did not
(`ran=0` for a task you edited), auto has a blind spot for that change (a data
file, an installed package, dynamic dispatch, a notebook-defined task): `reset`
it, or LOCK it with `code_version`.

Expensive tasks are guarded by default: an auto task whose last materialization
exceeded `settings.code_version_auto_expensive_s` (default 600s) stays cached on
a code change and WARNS with the exits (reset / `accept_code` / lock) instead of
silently recomputing.

`code_version` is now an opt-in LOCK, not a per-task ritual. Declaring it on a
task tells auto to STOP watching that task's source: the task reruns only on an
explicit bump, and a code edit without a bump WARNS (`StalenessWarning` naming
the changed symbol) instead of rerunning. Lock a task for (a) an EXPENSIVE
computation you want managed by deliberate bumps even below the guard threshold
(auto deletes and overwrites the old output on rerun); (b) logic auto cannot
see.

Do NOT lock a task that FUSES an expensive un-replayable fetch with cheap
deterministic parsing - a common shape, and the one where a lock actively misleads.
Every exit a lock offers reduces to "is this edit output-equivalent?", and there
that question is UNANSWERABLE: you cannot re-derive the parse without refetching,
so `accept_code` is a guess and the honest answer to any code change is "refetch".
SPLIT the task instead - a download task (pin it) feeding a parse task (let it
rerun freely). Prefer the split to the lock whenever the two halves have different
costs; reach for the lock only once the expensive part stands alone.

Locks toggle
FREELY: the `code_version` line itself is stripped by the AST normalization
(typing it in / deleting / bumping it is a token change, never a source edit)
and records store both the token and the source hashes, so adding or removing a
lock on unchanged code never recomputes and never ripples downstream; an edit
masked while locked-unbumped reruns the moment the lock comes off. A
locked task still reruns when an AUTO upstream rematerializes - the lock pins
only its OWN logic. Answer a lock's warning with
one of its exits: bump (output differs - recomputes and propagates downstream),
`flow.accept_code()` / `oryxflow.accept_code(instance)` (certain the output is
equivalent; when unsure, bump - it prints what it re-stamped, and the
instance/flow form also stamps baseline records for outputs that have none yet,
which is what clears an `output predates current code` warning after an
upgrade), or reset. The printed warning dedupes per process ON THE MESSAGE
(parameterized instances of one family and per-flow WorkflowMulti builds produce
identical text - it prints once; `result.warnings` lists each distinct message
once per run, only the event stream keeps every occurrence). Accepting
CASCADES: it re-stamps the anchor and its whole upstream tree; bare
`flow.accept_code()` covers the whole pipeline - every imported task family
that resolves with the flow's params, multi-final included, from a fresh
process - and a list of tasks works everywhere
(`flow.accept_code([FinalA, FinalB])`). On WorkflowMulti use the flow method
(`flow.accept_code()` covers all flows, `flow=...` for one) - the module-level
bulk form does not know the flows' parameters and cannot re-key records whose
symbols were renamed/moved (it reports those; use an instance); tasks reached
only DYNAMICALLY
(yielded inside a `run()`) need an explicit instance if they warn. Never write
a reset helper (`reset_if_code_changed`, a downstream-resetter). Global escape
hatch: `settings.code_version_auto = False` reverts to pure opt-in (only
explicit `code_version` / `flow.reset` rerun) - for projects where auto is too
fickle across many long-running tasks. On pre-26.7.12 (no auto, no
`code_version`) the manual `flow.reset(thatTask)` before running is the whole
discipline. Per-symbol granularity again: editing one helper or constant in a
shared `utils.py` / `cfg.py` recomputes exactly the tasks that reference it
(directly or via other helpers; `preview()` the pending band first), and
referencing another TASK in `requires()` is wiring, never a code dependency.
For the deeper model -
the reference-graph-vs-dependency-graph nuance of a lock's warning, and the
`reset_upstream(..., only=Family)` scopes - see the library's "Managing
workflows" docs (the `code-versioning` section).

**Keeping versions side by side**: on a LOCKED task, a string version +
`keep_versions = True` puts outputs under `data/Task/v<version>/`, so old
versions survive bumps - the compare-two-versions workflow. `keep_versions` keys
off explicit `code_version`, so auto tasks overwrite in place. Turning
`keep_versions` on relocates the task's output path, so it recomputes once.

**Changing a task's output columns** is just such a code edit: adding, removing,
or renaming a column reruns the task under auto (bump it if the task is locked)
plus a matching update to the docstring's output contract. Removing or renaming a
column breaks downstream tasks that read it - the rerun propagates and surfaces
the break as an error you fix in the same change. Subtler: changing what an
EXISTING column MEANS (recomputed values, new units) WITHOUT renaming it does not
error downstream - dependents recompute, but re-verify their semantics.

**Provenance / history (oryxflow >= 26.7.12)**: every run appends events to
`.oryxflow/events.jsonl` (plain JSONL; earlier months offload to
`events-YYYYMM.jsonl`, all history = glob `events*.jsonl`).
`oryxflow.events.print_status()` = session-start orientation, printed (pending
code warnings, last run per family, recent failures) - the default first call;
`oryxflow.events.status()` = the same facts as a dict for filtering (returns,
prints nothing - a bare call in a script shows nothing);
`oryxflow.events.runs(task_family='X',
last=2)` = diff the last two runs' params / code_version / source_hashes;
`task_ran` events carry the rerun reason (`output missing` /
`code change (auto: <file>::<symbol>)` / `code change (1 -> 2)` /
`code change (1 -> auto)` or `code change (auto -> 1)` (lock toggled off/on with
a source change to reconcile) / `upstream rerun`), git
SHA, duration. `self.logger`
lines are captured as `task_log` events, so logged scalars persist across
sessions.

### Important: Trust Auto File Management

oryxflow auto-handles file creation. DO NOT manually verify files after running
tasks.

- Don't: `flow.run()` then `ls data/TaskName/` or check paths
- Do: `flow.run()` then `df = flow.outputLoad(TaskName)`

If `flow.run()` completes without errors, files exist. Debug by loading data
with `flow.outputLoad()`, not by checking the file system.

---

## Advanced Patterns

### Pattern 1: Compare a named set of parameter variants (WorkflowMulti)

Use ONE `WorkflowMulti` keyed by name to run/compare a fixed set of param sets
(models, dates, cohorts) - one importable object, named access, no ad-hoc loop:

```python
# params is a dict KEYED BY FLOW NAME; each value is a param set
wf = oryxflow.WorkflowMulti(FinalTask, {
    'lgbm':    {'model': 'lgbm'},
    'xgboost': {'model': 'xgboost'},
    'rf':      {'model': 'rf'},
})
res = wf.run()                             # all flows; wf.run(flow='lgbm') for one
print(res.summary())                       # per-flow summary blocks; res['lgbm'] -> that flow's RunResult
wf.reset(tasks.Train, flow='rf')           # per-flow reset

df   = wf.outputLoad(tasks.Predict, flow='xgboost')  # one flow -> its output
alldf = wf.outputLoad(tasks.Predict)                 # omit flow= -> {name: output}
```

Notes:
- A **list** of param sets also works, but the keys become integer indices
  (`0, 1, 2`) - prefer the named dict so `flow=` and loaded results are labelled.
- If a dict *value* is a list, WorkflowMulti expands the cross-product of those
  values into separate flows (a param sweep).
- `wf.run()` returns a `{name: RunResult}` (a `MultiRunResult`) that also carries
  `.summary()`/`.success`, so `print(res.summary())` reads the same as a single
  flow; index `res['lgbm']` for one flow's `RunResult` to drill in (`.ran`/`.failed`).
- `oryxflow.runLoad(task, params=..., reset=False)` is the module-level
  run-and-load-in-one-call helper for a single param set (see below).

See the escalation note in SKILL.md for the full signatures - confirm against the
installed package (`inspect.signature(oryxflow.WorkflowMulti.outputLoad)`) rather
than assuming.

### Pattern 1b: Generate the param sets for a WorkflowMulti sweep

This builds a list of PARAM SETS (one independently-managed flow each) - it is not
dynamic task creation. To generate one TASK per item inside a single DAG, use the
fan-out in Pattern 3.

```python
import oryxflow.utils

params_base = {'threshold': 100}
params_list = oryxflow.utils.params_generator_dictlist(
    {'date': ['2024-01-01', '2024-01-02', '2024-01-03']},
    params_base
)
# Result: one dict per date, each with threshold=100

flow = oryxflow.WorkflowMulti(FinalTask, params_list)
flow.run()
```

### Pattern 2: Workflow Orchestration Task

Create a task that just runs dependencies without saving output:

```python
@oryxflow.requires(Task1, Task2, Task3)
class RunAll(oryxflow.tasks.TaskJson):
    def run(self):
        self.save({'status': 'complete', 'timestamp': datetime.now()})
```

### Pattern 3: Per-item fan-out (one task per list item)

Declare one dependency per value and let a combining task stack them. Full
decision table (fan-out vs `WorkflowMulti` vs a plain loop), hierarchies,
shared-input stacking, and the migration recipe: [dynamic-dags.md](dynamic-dags.md).

```python
@oryxflow.requires_each(RegionLoad, region=cfg.REGIONS)   # one RegionLoad PER region
class RegionCombine(oryxflow.tasks.TaskPqPandas):
    def run(self):
        self.save(self.inputLoadConcat())   # stacks branches, tags each with `region`
```

`requires_each` copies `RegionLoad`'s parameters onto `RegionCombine` MINUS
`region`, so downstream tasks go back to plain `@oryxflow.requires` and never learn
that N branches existed. Add a region to `cfg.REGIONS` and only that branch runs.

**ANTI-PATTERN - do not build a sub-`Workflow` inside a `run()` to iterate:**

```python
# WRONG: tasks started in run() are NOT dependencies
class MasterTask(oryxflow.tasks.TaskPqPandas):
    def run(self):
        for region in ['US', 'EU', 'ASIA']:
            sub_flow = oryxflow.Workflow(ProcessRegion, params={'region': region})
            sub_flow.run()   # invisible to preview(), to the run summary, to reset
```

Nothing can find those tasks: `flow.reset_upstream(MasterTask, only=ProcessRegion)`
invalidates nothing and reports no error, so you change a region's logic, reset
"just that step", re-run - and get the OLD numbers back with a green run. Declared
as a fan-out, every reset reaches every branch and a failure names its parameters.

### Pattern 4: Incremental Processing

```python
class IncrementalTask(oryxflow.tasks.TaskPqPandas):
    date = oryxflow.DateParameter()

    def run(self):
        prev_date = self.date - timedelta(days=1)
        try:
            prev_task = IncrementalTask(date=prev_date)
            df_prev = prev_task.output().load() if prev_task.complete() else pd.DataFrame()
        except Exception:
            df_prev = pd.DataFrame()

        df_new = pd.read_csv(f'data_{self.date}.csv')
        self.save(pd.concat([df_prev, df_new]))
```

---

## Configuration

### Environment-Based Configuration

```python
class MyTask(oryxflow.tasks.TaskPqPandas):
    env = oryxflow.Parameter(significant=False)  # 'dev' or 'prod'

    def run(self):
        if self.env == 'dev':
            df = pd.read_csv('sample.csv')
        else:
            df = pd.read_csv('full.csv')
        self.save(df)

flow = oryxflow.Workflow(MyTask, params={'env': 'dev'})
```

### Custom Task Directories

```python
class MyTask(oryxflow.tasks.TaskPqPandas):
    def output(self):
        return oryxflow.targets.PqPandas(path='/custom/path/output.parquet')
```

---

## Best Practices

### 1. Task Design

Do:
- Keep tasks focused on a single responsibility
- Name tasks for their OUTPUT (a noun: `OEWSWages`, `CleanedSales`,
  `TrainedModel`), not the verb they perform (see "Tasks > Naming")
- Write the docstring as real documentation: purpose + input/output contract +
  quirks. It explains intent; do NOT restate the run() code (a short snippet
  only when it is the clearest way to state a contract)
- Use type hints for clarity
- Validate inputs and outputs with assertions

Don't:
- Create monolithic tasks that do everything
- Use generic names like `GetData`, `Process`, `Task1`
- Paste the code into the docstring, or settle for a one-line "brief description"
- Skip error handling
- Assume data shape/columns without validation

```python
class CalculateFeatures(oryxflow.tasks.TaskPqPandas):
    """
    Calculate rolling averages and momentum features

    Input: DataFrame with columns ['date', 'value']
    Output: DataFrame with additional columns ['ma_30', 'ma_90', 'momentum']
    """
    def run(self):
        df = self.input().load()

        assert 'date' in df.columns, "Missing 'date' column"
        assert 'value' in df.columns, "Missing 'value' column"
        assert df.shape[0] > 0, "Empty DataFrame"

        df['ma_30'] = df['value'].rolling(30).mean()
        df['ma_90'] = df['value'].rolling(90).mean()
        df['momentum'] = df['value'].pct_change(30)

        assert not df['ma_30'].isna().all(), "All ma_30 values are NaN"
        self.save(df)
```

### 2. Parameter Management

Do:
- Define parameters at the top of the class
- Use appropriate parameter types
- Provide sensible defaults
- Use `significant=False` for non-data-affecting parameters
- Keep parameters in a separate config file/dict

Don't:
- Hard-code values that should be parameters
- Use parameters for values that never change
- Create too many parameters (makes task identity complex)

```python
# Good - centralized parameters
params = {
    'date': '2024-01-01', 'region': 'US', 'model_type': 'rf',
    'n_estimators': 100, 'test_size': 0.2
}
flow = oryxflow.Workflow(FinalTask, params=params)
```

### 3. Data Validation

Do:
- Assert expected columns exist
- Check for null values where unexpected
- Validate data shapes
- Check value ranges
- Log warnings for anomalies

```python
class ValidatedTask(oryxflow.tasks.TaskPqPandas):
    def run(self):
        df = self.input().load()

        required_cols = ['id', 'date', 'value']
        assert all(c in df.columns for c in required_cols), \
            f"Missing columns. Have: {df.columns.tolist()}, Need: {required_cols}"
        assert df['id'].isna().sum() == 0, "Null IDs found"
        assert df.shape[0] > 0, "Empty DataFrame"
        assert df.shape[1] >= 3, "Too few columns"
        assert df['value'].min() >= 0, "Negative values found"
        assert not df.duplicated('id').any(), "Duplicate IDs found"

        self.save(df)
```

### 4. Error Handling & Documentation

Use `self.logger` for in-task domain logging (and `oryxflow.enable_logging()` for
task lifecycle - see ml-patterns.md "Logging in ML tasks"); let the pipeline fail
natively (avoid try-except); give
every task a real docstring (purpose + input/output contract + quirks - see
"Task Design" above, and the SKILL "Task docstrings" rule).

---

## Avoiding silent data errors

The traps that produce a WRONG NUMBER with no exception - the dangerous kind,
because nothing fails. These bite the AI agent especially: an assumed column
meaning or an unvalidated join yields a confident, wrong analysis. Guard against
them explicitly.

### Validate every merge/join

A bad join key silently multiplies or drops rows and every number downstream is
wrong, with no error. Make the assumption explicit and let pandas enforce it:

```python
df = df_left.merge(df_right, on='id', how='left', validate='m:1')  # raises if right side isn't unique
assert len(df) == len(df_left), f"left join changed row count {len(df_left)} -> {len(df)}"
```

- Pass `validate=` (`'1:1'`, `'m:1'`, `'1:m'`) on EVERY merge - it raises if the
  key cardinality is not what you assumed (the usual cause of row blow-up).
- Check the row count before/after. A left join that grows the frame means the
  right key was not unique; an inner join that shrinks it means keys did not match
  (often a dtype or whitespace mismatch in the key - `'01'` vs `1`).
- After the merge, check `df[key].isna().sum()` on columns that should be fully
  populated - NaNs there flag unmatched rows.

### Verify before you conclude

Before stating ANY finding from a frame, look at it - do not assume its shape or
a column's meaning:

```python
print(df.shape, df.dtypes.to_dict())
print(df.isna().sum())
print(df.describe())            # ranges sane? a "rate" in [0,1] vs [0,100]?
```

Reconcile aggregates against a known total (sum of parts == whole; a group count
sums to the row count). A subtotal that does not reconcile means a filter, a
dropped NaN, or a double-counted join - find it before reporting the number.

### Quote computed numbers, never eyeball them

Every figure in prose or a report comes from the FRAME, pulled and rounded
explicitly - never read off a chart, guessed, or carried from memory:

```python
val = df.loc[df['sector'] == 'Tech', 'yield_dividend'].iloc[0]
print(f"Tech dividend yield: {val:.1%}")   # quote THIS, not "looks like ~6%"
```

A chart is for shape and direction; the number behind it comes from the data. If
a claim needs a value, compute it.

### Watch pandas index alignment

Arithmetic between two Series aligns on the INDEX, not on position. If two frames
have mismatched indices (one was filtered or sorted), `a['x'] - b['y']` pairs by
label and yields NaNs or silently wrong values - it does not error.

```python
# WRONG if df_a, df_b have different indices after a filter/sort
df_a['delta'] = df_a['value'] - df_b['value']
# Safer: align deliberately, or operate on .values for positional, or reset_index
df_a['delta'] = df_a['value'].values - df_b['value'].values   # positional, intentional
```

When combining columns from separately-built frames, `reset_index(drop=True)`
first, or merge on a key, rather than trusting positional alignment.

---

## Common Patterns for Data Science

### Train/Test Split

```python
class SplitData(oryxflow.tasks.TaskPqPandas):
    persists = ['train', 'test']
    test_size = oryxflow.FloatParameter(default=0.2)
    def run(self):
        from sklearn.model_selection import train_test_split
        df_train, df_test = train_test_split(self.inputLoad(), test_size=self.test_size, random_state=42)
        self.save([df_train, df_test], from_list=True)
```

### Feature Engineering

```python
@oryxflow.requires(CleanData)
class EngineerFeatures(oryxflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()
        df['hour'] = df['timestamp'].dt.hour
        df['value_lag1'] = df.groupby('id')['value'].shift(1)
        df['value_ma7'] = df.groupby('id')['value'].rolling(7).mean().reset_index(0, drop=True)
        self.save(df)
```

### Model Training & Evaluation

```python
@oryxflow.requires({'split': SplitData, 'features': EngineerFeatures})
class TrainModel(oryxflow.tasks.TaskPqPandas):
    persists = ['predictions', 'metrics']
    def run(self):
        df_train = self.input()['split']['train'].load()  # dep by name, output by name
        feature_cols = [c for c in self.inputLoad(task='features').columns if c.startswith('feature_')]
        model = RandomForestRegressor(n_estimators=100).fit(df_train[feature_cols], df_train['target'])
        df_test = self.input()['split']['test'].load()
        df_test['pred'] = model.predict(df_test[feature_cols])
        metrics = {'rmse': mean_squared_error(df_test['target'], df_test['pred'], squared=False)}
        self.save([df_test, pd.DataFrame([metrics])], from_list=True)
        self.saveMeta({'model': model, 'features': feature_cols})
```

---

## Debugging oryxflow Workflows

- **Task not running**: Already complete (cached) -> `flow.reset(TaskName); flow.run()`
- **Parameters not affecting task**: Check `significant=False` or parameter type
- **Cannot load multiple outputs**: Mismatch between `persists` list and `save()` count
- **Metadata not loading**: Not saved, or loading from wrong task (use `metaLoad(key=0)` for first dependency)

---

## Diagnosing a regression / version bump

On an unexpected `AttributeError` / `ImportError` / `TypeError` from the workflow
library, or right after a version bump, *before assuming a code bug*: confirm the
running library version with `oryxflow.__version__`, then grep the changelog for
the failing symbol and read entries from the installed version forward,
prioritizing `BREAKING:` entries.

- Library (source of truth for API/behavior) - changelog:
  `https://raw.githubusercontent.com/oryxintel/oryxflow/main/CHANGELOG.md`
  (rendered: https://docs.oryxflow.dev/docs/changelog/). In an
  editable checkout, `git log --oneline <old>..<new>` in the library repo is the
  live equivalent.
- Plugin (skill/guidance + compat contract) - changelog:
  `https://raw.githubusercontent.com/oryxintel/oryxflow-claude-plugin/main/docs/CHANGELOG.md`.
- **Authority: when the two disagree about library behavior, the library wins.** If
  the plugin's `Compatibility:` floor and `oryxflow.__version__` are violated (the
  running library is OLDER than the floor the skill assumes), say so - do not debug
  a phantom.
- After any library version change in a project, re-run `python run.py` as a cheap
  regression smoke test (this scaffold has no version pin and imports oryxflow
  across several files, so a library switch silently changes behavior).

Fetch the raw URLs (files are never auto-in-context); the raw URL returns clean
markdown, a `blob` URL returns HTML chrome. For the installed plugin you have the
skill on disk (no fetch); the fetch that matters is the LIBRARY changelog read
from inside a user's project. For BEHAVIOR (not just the changelog), the docs
site serves markdown to agents directly - `https://docs.oryxflow.dev/llms.txt`
to orient, any page + `index.md` for one page, `/llms-full.txt` for everything
(see "Additional Resources").

---

## Quick Reference

```python
# Create task
class MyTask(oryxflow.tasks.TaskPqPandas):
    param = oryxflow.Parameter()
    def run(self):
        self.save(result)

# Add dependencies
@oryxflow.requires(UpstreamTask)
class MyTask(oryxflow.tasks.TaskPqPandas):
    def run(self):
        df = self.inputLoad()

# Run workflow
flow = oryxflow.Workflow(FinalTask, params={'param': 'value'})
flow.run()
result = flow.outputLoad()

# Force re-run
flow.reset(TaskName); flow.run()

# Multiple outputs
class MyTask(oryxflow.tasks.TaskPqPandas):
    persists = ['a', 'b']
    def run(self):
        self.save([df_a, df_b], from_list=True)

# Metadata
self.saveMeta({'model': model})
meta = self.metaLoad(); model = meta['model']
```

---

## Project layout, code organization, and naming -> conventions.md

The project-structure deep dive (every file's role and how they wire together),
the subject-grouping rules for `eda/` / `utils/` / `viz/`, and the naming
conventions (columns, tasks, DataFrames) live in
[conventions.md](conventions.md) - the house-style companion to this library
reference. Load it when you organize files or name things.

## Additional Resources

- Official docs: https://docs.oryxflow.dev/ - **agent-readable by design**
  ([why](https://docs.oryxflow.dev/docs/ai-ready/)). Three ways in, cheapest
  first:
  - `https://docs.oryxflow.dev/llms.txt` - sectioned index of every page with
    one-line descriptions. Orient here, then fetch only what you need.
  - any page + `index.md` - clean markdown, no HTML chrome (e.g.
    `https://docs.oryxflow.dev/docs/managing-workflows/index.md`,
    `.../docs/tasks/index.md`, `.../docs/advparam/index.md`).
  - `https://docs.oryxflow.dev/llms-full.txt` - the ENTIRE corpus in one fetch.
    Use when the question is broad or you are converting a script wholesale.

  Both `llms*.txt` regenerate on every deploy, so they describe the currently
  RELEASED library - which is not necessarily the version installed in the
  project you are in. On a conflict, the installed package wins (check
  `oryxflow.__version__`, `inspect.signature`, `cls.__mro__`). Reach for the site
  when this skill is thin on a behavior; do not infer the answer, and do not
  assume a user has the library source on disk - a normal install has the wheel,
  not the docs.
- GitHub: https://github.com/oryxintel/oryxflow

---

## Summary

oryxflow: Reproducible, cacheable data science workflows. Tasks (classes with
`run()`), dependencies (`@oryxflow.requires()`), parameters (task variants),
auto-caching, multiple outputs (`persists`), metadata (models/configs).

**Use for**: Multi-step pipelines, ML workflows, reproducible research.
**Avoid for**: Simple scripts, real-time systems, single-step processes.

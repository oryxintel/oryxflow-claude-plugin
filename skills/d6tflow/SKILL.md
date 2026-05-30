---
name: d6tflow
description: >-
  Build and work with d6tflow data-science pipelines (Luigi-based: tasks,
  dependencies, parameters, caching, reproducible workflows). Use when working
  in a d6tflow project - editing tasks.py / flow.py / run.py / cfg.py /
  flow_params.py, adding or modifying pipeline tasks, running workflows with
  run.py, or analyzing outputs in visualize.py / visualize.ipynb.
allowed-tools: Read Edit Write Grep Glob Bash
shell: powershell
---

# Working with d6tflow Data Science Projects

d6tflow is a Python library (built on Luigi) for reproducible, cacheable data
pipelines with automatic dependency management and incremental computation.

**Key Principle**: Follow the established project structure and file
organization. DO NOT create ad-hoc scripts or inline commands for workflow
operations - use the existing project files.

For the full library reference (task types, advanced patterns, data-science
recipes, debugging table, deep project-structure walkthrough), see
[reference.md](reference.md). Load it on demand when you need detail beyond the
essentials below.

---

## Session Start: Read the Docs, Don't Re-Scan

This project carries its own memory in two files. Read them FIRST on every
session and treat them as the source of truth - do NOT re-explore the whole
project to rediscover what they already record.

- `docs/claude-project.md` - the pipeline: tasks, dependencies, parameters.
- `docs/claude-data-doc.md` - the data: schema, quality issues, business rules,
  quirks.

### Default invocation is LIGHTWEIGHT - do not auto-explore

When the skill loads (e.g. plain `/d6tflow`) with no specific task, orient
cheaply and then STOP. Do the minimum:

1. Read both docs if they exist.
2. If docs are missing, glance at the content files only to classify the project:
   does `tasks.py` still carry the `PLACEHOLDER SCAFFOLD` marker? -> fresh
   scaffold. Otherwise -> built pipeline (docs just not written yet).
3. Report the state in a sentence or two and ask what the user wants to do.

Do NOT, on a plain invocation: list/inspect `data/`, read raw source files,
write or run `eda/` scripts, or build the docs. That is expensive exploration
and it is the USER's call to start it - see "Deep exploration is opt-in" below.

When the user DOES give a concrete task: if docs are present and current, trust
them and open only the files that task touches. Don't broadly re-scan to
re-derive structure the docs already describe.

The docs are the cache. Keep them accurate and the per-session scan disappears.

Do NOT pre-create empty doc files. Their absence is the signal "not captured yet
-> scan." An empty-but-present file would defeat that check. Create a doc only
when you have real content to put in it, using the templates below.

### Deep exploration is opt-in

Full orientation - inspecting source data, profiling schema, and writing the
docs - runs ONLY when the user asks for it: `/d6tflow explore`, or a plain-
language request to "orient", "explore", "inspect the data", or "scan the
project". Until then, don't.

When explore IS requested:

- **Raw source data lives in `data/`** - typically loose files directly under it
  (`.csv`, `.xlsx`, etc.). Start there. Distinguish from task OUTPUT: d6tflow
  writes outputs into per-task subfolders as parquet (`data/GetData/*.parquet`,
  `data/Process/*.parquet`) - those are generated, not inputs, so ignore them
  when hunting for source data. The source path may point elsewhere via `cfg.py`;
  check it if `data/` has no raw files.
- Inspect schema with an `eda/` script (per the no-inline-Python rule), not ad
  hoc commands.
- Capture what you learn into `docs/claude-project.md` + `docs/claude-data-doc.md`
  (templates below) so the next session reads instead of re-exploring. This
  write-up is the payoff of exploring - don't skip it.

### Recognizing a fresh scaffold (the PLACEHOLDER marker)

Scaffold `.py` files are NOT blank - they ship runnable wiring so `python run.py`
works out of the box and the `from flow import flow` pattern is visible. The
placeholder logic (not the imports, which are real) carries a marker comment
directly above it so it cannot be mistaken for real work:
`# PLACEHOLDER SCAFFOLD - ...`

Use this marker to orient cheaply:

- **Wiring files** (`flow.py`, `run.py`, `cfg.py`) - real, identical-across-
  projects convention. Nothing to investigate; don't treat as project logic.
- **Content files** (`tasks.py`, `flow_params.py`) - if they still carry the
  `PLACEHOLDER SCAFFOLD` marker, nothing project-specific has been built yet.
  That marker IS the "fresh scaffold" signal - you do not need to read and judge
  the logic to decide. Your job is to REPLACE the marked block, not extend it.

When you build the real pipeline, delete the `PLACEHOLDER SCAFFOLD` lines along
with the dummy logic. Their absence (plus populated docs) signals "real project."

---

## Core Concepts (essentials)

1. **Tasks** - Classes with a `run()` method that inherit a d6tflow task type
   (e.g. `TaskPqPandas`, `TaskPickle`). They save outputs automatically via
   `self.save()`. Identified by class name + parameters.
2. **Dependencies** - Declared with the `@d6tflow.requires()` decorator;
   d6tflow runs tasks in the correct order. Load upstream data with
   `self.inputLoad()`.
3. **Parameters** - Make tasks dynamic and reusable. They affect task identity
   (caching) and auto-inherit to downstream tasks. Use `significant=False` for
   params that should not affect identity.
4. **Workflows** - Created via `d6tflow.Workflow(FinalTask, params=params)`.
   A single workflow instance is imported everywhere: `from flow import flow`.
   Caching prevents re-running completed tasks.
5. **Project-structure pattern** - Separation of concerns across config, task
   definition, execution, and analysis layers (see below).

---

## Project File Organization

```
project/
|-- tasks.py           # Workflow task definitions (GetData -> Process)
|-- cfg.py             # Global configuration and settings
|-- flow_params.py     # Workflow-specific parameters
|-- flow.py            # Workflow instance definition
|-- run.py             # Execute workflow tasks
|-- visualize.py       # Analysis script
|-- visualize.ipynb    # Analysis notebook
|-- .creds.yaml        # Protected credentials (optional, not committed)
|-- data/              # Data storage (task outputs + raw/exported data)
|-- docs/              # Project documentation
|-- reports/           # Output reports and plots (version controlled)
`-- reports/render/    # Temporary report output (not version controlled)
```

**Central Pattern**: `from flow import flow`  # Import everywhere

File flow: `cfg.py` -> `flow_params.py` -> `tasks.py` -> `flow.py` ->
`run.py` / `visualize.py` / `visualize.ipynb` (all import the same `flow`).

---

## Workflow Operations: Use Existing Files

DO NOT create ad-hoc Python scripts or inline bash commands.

NEVER do this:
```bash
python -c "import d6tflow; flow = d6tflow.Workflow(...); flow.run()"
```

ALWAYS do this:

- **Modify workflow logic** - Edit `tasks.py` (task classes),
  `flow_params.py` (parameters), or `flow.py` (which final task runs).
- **Run the workflow** - Edit `run.py` if needed (e.g. uncomment reset calls),
  then run `python run.py`.
- **Analyze outputs** - Edit `visualize.py` then run `python visualize.py`,
  or use `visualize.ipynb` interactively.

NEVER write inline Python (no `python -c`, no inline snippets). ALL test / EDA /
exploratory code goes in a file under `eda/{meaningful-file-name}.py` and is
then executed (`python eda/{name}.py`). Give the file a descriptive name for the
exploration it performs.

### Python REPL / script commands
```python
from flow import flow
import tasks

flow.preview()                    # Preview what will run
flow.run()                        # Run workflow
flow.complete()                   # Check if complete (True/False)
flow.reset(tasks.TaskName)        # Force re-run from task
df = flow.outputLoad(tasks.Task)  # Load task output
```

**Trust auto file management**: if `flow.run()` completes without errors, the
output files exist. Debug by loading with `flow.outputLoad()`, NOT by checking
the file system.

---

## Code Style: ASCII Only

DO NOT use Unicode symbols (emojis, checkmarks, special characters) in code or
print statements - they cause encoding issues on Windows.

NEVER:
```python
print("Success!")   # with a checkmark/emoji prefix
```
ALWAYS:
```python
print("SUCCESS: Operation completed")
print("WARNING: Issue detected")
print("ERROR: Operation failed")
```

### No try/except wrapping

DO NOT wrap code in try/except blocks. Let it fail natively so errors surface.
Exceptions (only): when the user expressly asks for it, or in temporary / EDA
code under `eda/`.

### Assume given file paths exist

When the user provides a file path, assume it exists - do NOT add existence
checks (`os.path.exists`, etc.) before reading it. If it does not exist, the
read will raise an error, which is the desired behavior.

---

## Reading Locked Excel Files

When loading an Excel file that is currently open and locked (read fails with a
permission/sharing error), DO NOT work around it (e.g. copying to a temp file).
Instead, STOP and ask the user to close the file, then retry the read.

---

## Common Workflow Patterns

### Add a new task
1. Define the task in `tasks.py`:
```python
@d6tflow.requires(UpstreamTask)
class NewTask(d6tflow.tasks.TaskPqPandas):
    """Brief description of what this task does"""
    param1 = d6tflow.Parameter()

    def run(self):
        df = self.inputLoad()
        # process data
        self.save(df_processed)
```
2. Add parameters to `flow_params.py`: `params['param1'] = 'value'`
3. If it is the new final task, set `task = tasks.NewTask` in `flow.py`.
4. Document it in `docs/claude-project.md`.

### Modify an existing task
1. Edit the task in `tasks.py`.
2. Force re-run: uncomment `flow.reset(tasks.ModifiedTask)` in `run.py`.
3. Run `python run.py`.
4. Update `docs/claude-project.md`.

### Change parameters
1. Edit `flow_params.py`: `params['param'] = 'new_value'`.
2. Run `python run.py` (the change is auto-detected).
3. Update `docs/claude-project.md` if the parameter meaning changed.

### Debug workflow issues
```python
flow.preview()                         # Preview what will run
flow.complete()                        # Check completion
df = flow.outputLoad(tasks.Task)       # Inspect outputs
flow.reset(tasks.Task); flow.run()     # Force re-run
```

---

## Quick Reference

**Task types**: `TaskPqPandas` (DataFrames as Parquet, FASTEST - default),
`TaskPickle` (any Python object: models, dicts, lists), `TaskJson`
(dicts / simple structures). Full table in [reference.md](reference.md).

**Loading**: `df = self.inputLoad()` (single), `df1, df2 = self.inputLoad()`
(multiple), `meta = self.metaLoad()` (metadata).

**Saving**: `self.save(df)` (single), `self.save([df1, df2], from_list=True)`
(multiple), `self.saveMeta({'model': model})` (models/configs).

---

## Project Documentation to Maintain

These files are per-project (not part of this skill). They are the session cache
read at "Session Start" above - keeping them current is what lets future
sessions skip re-scanning, so update them as part of the same change, not later:

- `docs/claude-project.md` - THIS project's tasks, dependencies, parameters.
  Update after adding tasks or changing parameters/dependencies/logic.
- `docs/claude-data-doc.md` - Data findings: schema, quality issues, business
  rules, quirks. Update when discovering schema details or data issues.

If you finish a change without updating these, the next session pays the scan
cost you just avoided. Treat the doc update as part of "done."

### Doc templates

Use these skeletons when first creating the docs. Keep them short and factual -
they are a cache to read fast, not prose. Fill what is known; for a fresh
scaffold, say so plainly (e.g. "boilerplate GetData/Process, no real data yet").

`docs/claude-project.md`:
```markdown
# <project> - Pipeline

## Goal
<1-2 lines: what this workflow produces and why>

## Pipeline (task DAG)
<UpstreamTask> -> <DownstreamTask> -> <FinalTask>

| Task | Type | Depends on | Does |
|------|------|-----------|------|
| GetData | TaskPqPandas | - | <what it loads/produces> |
| Process | TaskPqPandas | GetData | <transformation> |

## Parameters
| Name | Type | Default | Meaning |
|------|------|---------|---------|
| <param> | <Parameter type> | <default> | <what it controls> |

## Flow config
- Final task: <tasks.X>  (set in flow.py)
- Params source: flow_params.py

## Open questions / TODO
- <unknowns, placeholders still to replace>
```

`docs/claude-data-doc.md`:
```markdown
# <project> - Data

## Sources
- <file / DB / API>: <what it is, how accessed>

## Schema
| Column | Type | Notes |
|--------|------|-------|
| <col> | <dtype> | <meaning, units> |

## Quality issues & quirks
- <nulls, dupes, encoding, outliers, gotchas>

## Business rules
- <domain rules that affect transforms>

## Open questions
- <unresolved data questions>
```

---

## Additional Resources

- [reference.md](reference.md) - comprehensive d6tflow patterns and reference.
- d6tflow docs: https://d6tflow.readthedocs.io/
- d6tflow GitHub: https://github.com/d6t/d6tflow

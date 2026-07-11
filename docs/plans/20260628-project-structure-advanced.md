# Document the advanced / multi-module + productionize structure

> SELF-CONTAINED PLAN for a fresh session. All findings, concrete code patterns,
> file anchors, and rationale needed to implement are embedded below - you should
> not need to re-explore the example projects. Repo root: the oryxflow plugin repo
> (`skills/oryxflow/`, `docs/design/`, `resources/template-minimal/`). Read
> `docs/design/architecture.md` first (the repo map). ASCII-only, wrap prose at
> ~78 cols (repo convention).

## Context

The plugin scaffolds and documents a **flat** project: one `tasks.py`, `run.py`,
`flow.py`, `flow_params.py`. Right for the ~80% of projects that stay
research-only. But ~20% grow - mostly when something goes to "prod" - and the
docs give almost no guidance for that moment: how a long `tasks.py` should be
organized/split, how prod and experimentation coexist in one directory, and how
a research project (often messy notebooks) gets productionized. The current
`conventions.md` "Alternative Structures" section is thin, internally
inconsistent (shows a `tasks/` package AND suffixed `flow_*`/`run_*` files), and
predates the by-subject code-org convention. Data scientists are typically weak
at code organization, so the coding agent should be **proactive** here.

We are *defining* a coherent best practice (not mirroring the example projects -
some are messy), then threading it through the load-tiered skill files.

### Evidence (six real projects studied during planning - for grounding only)

| Project | tasks shape | Notable |
|---|---|---|
| fundamentals 2026-06-22 (plugin-built R&D) | 149L, 3 tasks, 1 naming family | flat, comfortable |
| ai-impact 2026-05 (plugin-built R&D) | **531L, 10 tasks, 2 branches, ONE file** | branches divided by **comment section-headers** + naming families; no strain |
| consumer-project-20250322 (2025 prod) | 35 tasks, ONE `tasks.py` + `llm/` subdir pkg | `params`+`params_prod` in one `flow_params.py`; `RunAll`/`RunAllModelPredictCurrent`/`RunAllModelPredictCurrentProd`; selective resets; `env=prod/dev` |
| flow-crs (2021 prod) | 8 `tasks_*.py` (tbl/universe/bq/athena/model/backtest/rpt) | split by source/platform/stage; direct imports, **no aggregator** |
| project-b (2020 + app) | `tasks.py` + `tasks_13f.py` | streamlit `app-streamlit.py` at root + `cfg_app.py` + `devops/app-run.sh`; app imports flow, runs it, `outputLoad`s |
| (old projects predate `flow_params`) | inline Workflow in run scripts | legacy; we KEEP `flow.py`/`flow_params.py` |

Key takeaways that shaped the model: a sectioned single file scales past 500
lines fine (ai-impact); splitting is by source/subsystem (flow-crs, project-b)
or phase; nobody uses a re-export aggregator; prod coexistence = `params_prod` +
a `RunAll...Prod` task + selective resets + `env=`.

## The best-practice model we are codifying

**1. Scaling `tasks.py` - a graduated progression (the headline).** Do NOT jump
to splitting files. Each step is deferred until the prior strains:
- **a. One `tasks.py`, chain-ordered** (the flat start).
- **b. Naming families** (broad->narrow prefixes - existing convention:
  `Features*`, `Model*`, `Data*`) cluster related tasks.
- **c. Comment section-header blocks** divide branches/phases within the one
  file. Cheap intermediate organizer; carries a file past ~500 lines
  (ai-impact: 531L/10 tasks/2 branches, no strain); agent-friendly (headers
  orient + are unique edit anchors). Style:
  ```python
  # ===========================================================================
  # Model layer - train + evaluate (parallel to the feature layer above)
  # ===========================================================================
  ```
- **d. Split into modules** only when genuinely long (rough signal ~1000 lines /
  ~20+ tasks, or "scrolling to find a task" pain) OR a separable subsystem
  emerges. **Cut along the section seams from step c.** Cache-safe: task identity
  is the class name (`task_family`), NOT the module path, so moving a class does
  NOT invalidate its `data/<Class>/` cache. (VERIFY before asserting - see
  "Verify during implementation".)

**2. Two orthogonal split axes (state both plainly).**
- **Phase axis** (break up the main pipeline): `tasks_features.py` /
  `tasks_model.py` / `tasks_eval.py`. Imports flow **upstream-only**
  (`tasks_model` imports `tasks_features`) -> acyclic by construction.
- **Subsystem axis** (carve off a separable concern): a distinct data
  source/platform (`tasks_13f.py`), an app, an LLM/reporting layer. When the
  subsystem bundles its own helpers/config/templates, give it a **subdir
  package** (`llm/tasks_llm.py` + `llm/prompts.py` + ...), matching the existing
  by-subject `eda/utils/viz` grouping.

**3. Keep a slim `tasks.py` spine when you split (NOT a re-export aggregator).**
It holds the pipeline-overview module docstring (the project-goal home our
convention already mandates) + the orchestration tasks (`RunAll`,
`RunAll...Prod`), and IT imports the phase modules. Phase/subsystem modules hold
the work; cross-module deps import the specific sibling module directly. No
aggregator that re-exports everything (all studied projects use direct imports;
avoids cycles). Concrete:
```python
# tasks.py (the spine, after splitting)
"""<Project goal: what the pipeline produces and why - top-level project doc.>"""
import oryxflow
import cfg
import tasks_features, tasks_model, tasks_eval   # phase modules (the work)

@oryxflow.requires(tasks_eval.ModelEval)
class RunAll(oryxflow.tasks.TaskJson):
    """Run the full pipeline; completion marker."""
    def run(self):
        self.save({'status': 'complete'})
```
```python
# tasks_model.py (a phase module - imports UPSTREAM phase only -> acyclic)
"""Model layer: train + in-sample performance."""
import oryxflow
import cfg
import tasks_features

@oryxflow.requires(tasks_features.FeaturesTransform)
class ModelTrain(oryxflow.tasks.TaskPqPandas):
    ...
```

**4. `flow.py` / `flow_params.py` are kept at every tier; params in one place.**
`flow_params.py` holds experiment `params` (comment-toggle) AND a frozen
`params_prod` dict. No `flow_params_<topic>.py` unless genuinely complex.
```python
# flow_params.py
import cfg

# Experiment params (toggle by commenting; last assignment wins)
params = dict(sector='Residential')
params['model'] = 'rf'
params['env'] = cfg.env
params['period_current'] = '2025Q4'

# Frozen prod params - ONE source of truth, imported by the prod orchestration
params_prod = dict(
    sector='Residential', env='prod', model='rf',
    transformx='chg_yoy_rank', transformy='rankpct', regularize=True,
    period_current=params['period_current'],
)
```

**5. Prod vs experiment coexistence (the "going to prod" lifecycle).**
- `params_prod` defined ONCE in `flow_params.py`; the prod orchestration task
  IMPORTS it (`from flow_params import params_prod`) - NOT re-hardcoded inline
  (this fixes a real duplication in the consumer-project example).
- A `RunAll<Final>Prod` orchestration task loops the prod variants and does
  **selective resets** (refresh the data layers for fresh data; keep `ModelTrain`
  frozen/cached); its experiment twin uses `params`.
- `env=prod` / `env=dev` data segregation via `cfg.env`.
- A documented periodic-refresh protocol (refresh raw inputs, bump
  `period_current`, run the Prod task).
```python
# tasks.py spine - prod orchestration
from flow_params import params_prod

class RunAllModelPredictCurrentProd(oryxflow.tasks.TaskExcelPandas):
    """Prod run: frozen params, all variants, fresh data, model stays cached."""
    period_current = oryxflow.Parameter()
    def run(self):
        dfl = []
        for sector in cfg.sectors:
            params = {**params_prod, 'sector': sector,
                      'period_current': self.period_current}
            flow = oryxflow.Workflow(tasks_predict.ModelPredictCurrent,
                                    params=params, env='prod')
            flow.reset(tasks_features.DataSource)  # refresh data layer ONLY
            # do NOT reset ModelTrain -> frozen model
            flow.run()
            dfl.append(flow.outputLoad(tasks_predict.ModelPredictCurrent))
        self.save(pd.concat(dfl))
```

**6. Adding an app / reporting subsystem.** App at the project ROOT by default
(same import/path-resolution reason as notebooks) + its own `cfg_app.py` + a
launch script; it imports the flow, runs it, and `flow.outputLoad(tasks.X)`s
outputs - NEVER reads `data/` directly.
```python
# app-streamlit.py  (project root; launch: streamlit run app-streamlit.py)
import streamlit as st
import oryxflow
import cfg, cfg_app
import tasks
from flow_params import params_prod

params = {**params_prod, 'portfolio': st.session_state.portfolio}
flow = oryxflow.Workflow(tasks.Screen, params=params)
flow.run()
df = flow.outputLoad(tasks.Screen)   # load outputs; never read data/ directly
```

**7. Proactive agent behavior.** Nudge to graduate on concrete triggers - **going
to prod**, **a separable subsystem appearing** (app / LLM / alt source), or a
**genuinely long file** - NOT on raw task count (one sectioned file scales far).
Nudge mid-edit; stay silent on plain orientation (keeps the existing
"don't auto-explore" rule).

## Changes by file (load-tiered)

### `skills/oryxflow/conventions.md` - layout / code-org home (items 1-4, 6)
- **Replace** the "Alternative Structures" section (currently the LAST section,
  the `large projects` / `tasks/` package + `flow_*`/`run_*` multi-workflow code
  blocks - locate by the `### Alternative Structures` heading near end of file)
  with a new **"Scaling up: organizing a growing project"** section covering the
  graduated progression (1a-d), the two axes (2), the `tasks.py` spine + direct
  imports/no aggregator + cache-safe-move (3), `params`+`params_prod` in one
  `flow_params.py` (4), subsystem subdir packages, and the app pattern (6).
- Also fix the older inline hint in the `tasks.py` file-description block
  ("can split into multiple files ... `tasks_etl.py`, `tasks_models.py`") to
  point at the new section instead of giving a second, divergent rule.
- REUSE, don't restate, the existing "Code organization: group by subject"
  section (it already defines subject = task/dataset/concept, subdir packages,
  the import contract, casing) - the subsystem axis IS that rule applied to
  tasks. Cross-link it.
- Keep `env=prod/dev` to a one-line mention here; depth -> ml-patterns.

### `skills/oryxflow/ml-patterns.md` - ML-prod lifecycle (item 5) + notebook path
- Add a **"Productionizing: prod vs experiment"** section: `params_prod` (single
  source), `RunAll` / `RunAll...Prod` orchestration (import `params_prod`, loop
  variants, selective resets), `env=prod/dev`, periodic-refresh protocol. Use the
  item-5 code above.
- Add a short **"Productionize a research project / notebook"** subsection (the
  data/ML-eng persona): sort messy notebook cells into phase tasks (load ->
  features -> model -> eval -> predict - the bins this file ALREADY defines in
  its "Task organization checklist"), wire the DAG, then add the prod
  orchestration. Connect to SKILL.md's no-inline-Python rule (cells become tasks
  / `eda/` probes, never `python -c`).
- Upgrade the existing checklist item 7 ("7. RunAll - orchestration task
  (aggregates all steps).", near end of file) to point at the new section and
  mention the prod twin.

### `skills/oryxflow/SKILL.md` - essentials only (keep every addition minimal)
- In the "Project File Organization" / "Code organization" area (the block around
  the file-tree + "group supporting code by SUBJECT" paragraph), add ONE line
  pointing to conventions.md "Scaling up" for when/how a project graduates
  (section-headers -> split; spine; prod params).
- Add the proactive-nudge rule (item 7) as a tight imperative (trigger + the
  rationalization it blocks + stay-silent-on-orient) - likely near the existing
  "Default invocation is LIGHTWEIGHT" / orientation rules so it inherits that
  framing.
- Add one or two example invocations to the existing "Example invocations to
  offer" Build group (around the "Build:" bullet), e.g. `"split tasks.py along
  its sections into modules"`, `"set up a prod run with frozen params"`.
- Do not bloat: if any addition grows, push depth to conventions.md/ml-patterns.

### `docs/design/design-notes.md` - rationale (WHY)
Record: graduation over a second template (80/20 + restructure-as-it-grows +
maintenance cost of a second scaffold); section-headers-then-split, with headers
as the cut seam; `tasks.py` spine vs re-export aggregator (and the goal-docstring
home problem it solves); phase vs subsystem axes; `params_prod` single-source
(fixing the example's duplication); the proactivity triggers; and the
agent-ergonomics reasoning (a sectioned single file is good for the agent up to a
threshold; acyclic upstream-only imports; cache-safe moves).

### `docs/design/architecture.md` - keep the map current
Update the "Where to change X" playbook + the component/load-tier notes so the
new guidance is locatable: conventions.md owns scaling LAYOUT; ml-patterns.md
owns the PROD lifecycle. Small edit (add/adjust a row or two).

### `docs/CHANGELOG.md` + `.claude-plugin/plugin.json` - release
These are skill changes installed copies must pick up, and today (2026-06-28) is
a new day vs the current top changelog section (`26.6.22`). Start a NEW top
section `## [26.6.28] - 2026-06-28` with `### Added` / `### Changed` bullets
summarizing the scaling/prod guidance, and set `plugin.json` `version` to
`26.6.28` (top changelog version and `plugin.json` version MUST match).

### `resources/template-minimal/CLAUDE.md` (optional, low priority)
One line noting the project can scale (section-headers -> split) with a pointer to
the plugin's "Scaling up" guidance. Scaffold-change version-bump rule is already
satisfied by the bump above.

## Verify during implementation
- **Cache-on-move claim**: confirm oryxflow/luigi keys identity on class name
  (`task_family`), NOT module path, so moving a class between `tasks_*.py`
  preserves its `data/<Class>/` cache. Confirm (inspect oryxflow behavior or a
  quick move test) BEFORE asserting it in the docs. The existing "Stale caches on
  rename" note stays - RENAME still orphans the old cache; only MOVE is safe.
- ASCII-only + ~78-col wrap in every edited file.
- Keep `SKILL.md` lean - depth belongs in conventions.md / ml-patterns.md.

## Verification (end-to-end)
- `claude plugin validate .` passes; changelog top version == `plugin.json`
  version (`26.6.28`).
- Re-read the three edited skill files as a user would: SKILL.md still scans
  fast; conventions.md "Scaling up" reads as one coherent progression with no
  leftover contradiction (old `tasks/`-package / `flow_*` blocks gone); the
  `tasks.py` file-description hint now agrees with it; ml-patterns.md
  "Productionizing" section is self-contained and the notebook path is
  actionable.
- Dry-run the intended agent behavior mentally against the studied projects:
  given ai-impact (531L, sectioned, one file) the rule says DON'T split yet;
  a "we're going to prod" request -> offer `params_prod` + `RunAll...Prod`;
  "add a streamlit app" -> scaffold app-at-root + `cfg_app.py` + launcher.
- Confirm cross-references resolve (SKILL.md -> conventions.md "Scaling up" and
  -> ml-patterns.md "Productionizing"; architecture.md playbook rows point to the
  right files; conventions.md "Scaling up" <-> "Code organization: group by
  subject").

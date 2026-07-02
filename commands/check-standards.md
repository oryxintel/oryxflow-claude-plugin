---
description: Check d6tflow project code against the house standards for readable, reliable code - naming (task / column / variable / module), code style (ASCII-only, self.logger, no try/except, off-the-shelf libraries), and docstring contracts. Evaluates and recommends a concrete fix per issue; applies only what the user approves. Use before or after writing a task.
disable-model-invocation: true
---

# Check d6tflow code against the house standards

Check the project's code against the `d6tflow` skill's house standards for
readable, reliable code - the NAMING rules (tasks, columns, variables,
`eda`/`utils`/`viz` modules), the CODE STYLE rules, and DOCSTRING contracts.
This is a read-first, evaluate-and-recommend review: you surface findings with a
concrete fix each, and edit ONLY what the user approves. Run it before committing
a change, or on code you are about to write to sanity-check the names first.
Target directory: `${CLAUDE_PROJECT_DIR}`.

Companion command: `/d6tflow:cleanup-tasks` reviews code ORGANIZATION (repeated
calls / reused data that should be consolidated into a cached task, task
decomposition). This command stays on NAMES + STYLE + DOCSTRINGS - do not drift
into re-architecting the pipeline; note an organization smell as a one-line
pointer to `cleanup-tasks` and move on.

## 1. Load the rules first (they are the rubric)

Load the `d6tflow` skill if it is not active, then read the source of truth for
the rules so you review against the ACTUAL conventions, not your priors:

- `conventions.md` "Naming" - columns, tasks, variables, modules (the Don't/Do
  table and the worked count/ratio family are the crux).
- `SKILL.md` "Code Style" and "Naming tasks" / "Task docstrings".

If the plugin / skill is not available at all, STOP and tell the user - this
command needs the rubric.

## 2. Determine scope

- An explicit `$ARGUMENTS` (a file, a task name, or `all`) sets the scope.
- Otherwise default to the CHANGED code: the working-tree diff plus untracked
  pipeline files (`git status`). Reviewing everything on every run is noise;
  focus on what is new or edited unless the user asks for `all`.

Read the files in scope. Do not run the pipeline - this is a static review.

## 3. Check every dimension against the rubric

The rules themselves live in the files you loaded in step 1 - review AGAINST
those, do not work from a restated copy (it would drift from the skill). This
list only guarantees COVERAGE: walk all six dimensions so none is skipped, and
for each, the named rubric section is the authority. For every hit capture
`file:line`, the offending name/code, the rule it breaks, and a concrete fix
(the actual rename / rewrite, not "consider renaming").

- **Task names** (`tasks.py` classes) - `conventions.md` "Task naming" +
  `SKILL.md` "Naming tasks". Highest-yield trap: a verb/generic name
  (`GetData`, `Process`) instead of an output noun, or a leftover scaffold
  `GetData`/`Process` with real logic written into it.
- **Column names** (in `.agg(name=...)`, `.rename(columns=...)`, output frames,
  the docstring `Out:` list) - `conventions.md` "Column naming"; the Don't/Do
  table and the worked count/ratio family ARE the test. Highest-yield trap: a
  leading stat/unit (`avg_`/`pct_`/`n_`/`min_`) that should be a trailing suffix.
- **Variable / DataFrame names** - `conventions.md` "DataFrame / variable
  naming". Trap: variant-first (`df_gross_returns`) instead of family-first
  (`df_returns_gross`).
- **Module names** (`eda/`, `utils/`, `viz/`) - `conventions.md` "Code
  organization" naming rules. Trap: a bare-verb filename (`verify.py`) or one
  carrying the redundant subject token, and non-snake_case of the class.
- **Code style** - `SKILL.md` "Code Style". Trap: non-ASCII; `print` or raw
  `from loguru import logger` inside a task instead of `self.logger`;
  `try/except` wrapping; hand-rolled math over an off-the-shelf library; inline
  `python -c` / ad-hoc scripts.
- **Task docstrings** - `SKILL.md` "Task docstrings". Trap: a one-line
  code-restatement with no in -> out contract (inputs + saved columns/keys).

## 4. Report, then apply

Present findings grouped by dimension, most-actionable first. For each:
`file:line` - the issue - the rule - the concrete fix. Keep it a review: do NOT
edit yet. If nothing violates, say so plainly rather than inventing nits.

Then ask which fixes to apply. On approval, apply with `Edit` (surgical). Two
cautions when a fix is a RENAME:
- Renaming a column or variable means updating EVERY reader in scope, plus the
  docstring `Out:` list - do them together or not at all.
- Renaming a TASK class orphans its `data/<OldName>/` cache and breaks
  `@d6tflow.requires` / `tasks.X` references - flag this as more than a
  find-replace and let the user confirm (the skill's "Stale caches on rename").

## 5. Finish

Summarize what was flagged, what was fixed, and what was left as a note
(including any organization smell you punted to `/d6tflow:cleanup-tasks`).

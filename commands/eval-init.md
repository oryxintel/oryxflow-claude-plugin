---
description: Scaffold an eval from the bundled eval template into the repo's evals/ project (shared _env.py and cache once per repo, then one run_eval_<name>.py and one <name>/ folder per eval; skip-existing, never overwrite), fill it from the eval plan, and prove the wiring with a 3-call smoke run.
disable-model-invocation: true
---

# Scaffold an eval from the plan

Copy the bundled eval template into the repo's `evals/` directory and wire it to
the decisions already recorded in that eval's plan, so the user has a runnable
harness.

- Template source: `${CLAUDE_PLUGIN_ROOT}/resources/template-eval/`
- Target: `${CLAUDE_PROJECT_DIR}/evals/`
- `<name>` comes from the user's argument. With none, name it after the surface
  under test (`prompt_triage`, `summarizer`) and say which name you chose. It is
  a Python package name: lowercase, underscores, no dashes.

This command COPIES FILES. `/oryxflow:eval-plan` is the command that DECIDES -
what is measured, the guardrail, the baseline. Do not re-decide any of that here;
read it out of the plan and wire it in.

## The layout you are building

`evals/` is ONE oryxflow project; each eval is a folder inside it:

```
evals/                         # the project dir - every eval is launched from here
  _env.py                      # ONCE per repo: credentials + import path
  data/                        # ONE cache for every eval (created on first run)
  run_eval_<name>.py           # per eval: 3 lines, ev.cli(<Name>Eval)
  <name>/                      # per eval: a package
    __init__.py  README.md  eval.py  agent.py  cases.csv  fixtures/  results/
```

Why: the costly part of an eval in an app repo is the setup (where production code
is importable from, how credentials load), and written per eval it gets re-derived
and drifts. `_env.py` holds it once. Eval classes share the cache, so each must be
uniquely named.

The template mirrors it: `_env.py`, `run_eval_NAME.py` and the `NAME/` folder.

## 1. Pre-flight - there must be a plan

Read `evals/<name>/README.md`.

- **It exists.** Use it. Every declaration you write below comes from it.
- **It does not exist.** Run the `/oryxflow:eval-plan` flow INLINE - gather the
  same context and ask the same questions. Show the resulting plan and WAIT for a
  yes. Write NOTHING - not the README, not a template file - until the user
  confirms. On confirmation, write `evals/<name>/README.md` and continue.

Never skip the plan and scaffold from your own guesses. An eval whose metric was
never argued measures whatever the scaffold happened to declare.

Before writing any oryxflow or pydantic-evals code below, read the docs for the
API you are about to use, not its source: https://docs.oryxflow.dev/llms.txt
(the LLM evals pages) and https://pydantic.dev/docs/ai/evals/ . Read source only
to settle what the docs leave open. The INSTALLED version wins over the docs;
report any mismatch.

## 2. Copy the template (skip-existing, never overwrite, with renames)

Three copies, each skipping anything that already exists in the target - that is
what makes re-running this command safe on an eval the user has already edited:

| from the template | to | when |
|---|---|---|
| `_env.py` | `evals/_env.py` | only if absent (first eval in this repo) |
| `run_eval_NAME.py` | `evals/run_eval_<name>.py` | only if absent |
| `NAME/` (whole tree) | `evals/<name>/` | files that are absent |

Do each with a SHELL COPY COMMAND. Do NOT read template files into context and
re-write them with the Write tool - that is slow and can corrupt files. Pick the
command by PLATFORM and use it consistently:

- **Windows (default here): `robocopy`** via the PowerShell tool. Directory:
  `robocopy "<src>\NAME" "<dst>\<name>" /E /XC /XN /XO`. Single file:
  `if (-not (Test-Path "<dst>")) { Copy-Item "<src>" "<dst>" }`.
- macOS / Linux: `cp -rn "<src>/NAME/." "<dst>/<name>/"`; a single file with
  `cp -n "<src>" "<dst>"`.

**robocopy exit codes are NOT shell errors.** 0-7 is SUCCESS (1 = files copied,
0 = nothing to copy); only >= 8 is a real failure. Do not retry with a different
command on exit code 1.

Then diff the source and target file lists to know what was created vs skipped,
via shell listings, not by reading file contents. `README.md` is NOT in the
template - the plan wrote it.

## 3. Fill the template from the plan

Edit the COPIED files, never the template.

- **`evals/_env.py`** - only when you just created it. Fill its two placeholders
  from the plan's `Running it` section:
  - **where production code is importable from.** Prefer installing the package
    that owns it (`pip install -e <dir holding its pyproject.toml>`), which needs
    nothing in `_env.py`. Add a path only when installing is not possible.
  - **how credentials load** - by ABSOLUTE path anchored on `ROOT`, never relative
    to the working directory. A loader that resolves relative to the working
    directory finds nothing from `evals/` and every case raises. Never write a key
    into the file; point at where it is stored.

  If `_env.py` already existed, read it and do not change it; if this eval needs
  something it lacks, say so and propose the edit.
- **`evals/run_eval_<name>.py`** - replace `NAME` with `<name>` and `PromptEval`
  with the eval's class name.
- **`agent.py`** - import the function under test from PRODUCTION code at the
  entry point the plan names, after `_env`. Import it; do not copy it, do not
  re-render its prompt here. A second copy of the instructions inside `evals/`
  drifts from the live ones and then measures nothing. Return EXACTLY the columns
  the plan's `The table` section lists, and carry anything a scorer needs into
  the output - the tool calls made, if one checks them: outputs are stored and
  re-scored later, the run's trace is not.
- **`eval.py`** - declare:
  - **the class name**: `<Name>Eval`, unique across `evals/` (every eval shares
    one cache, keyed on the class name). Grep the other evals before choosing.
  - the arm parameters (the axis the plan compares), one oryxflow Parameter each,
    with the baseline arm's value named `baseline` (or set `baseline = '<arm>'`):
    the verdict reports every arm against it;
  - `metric = ev.Metric(...)` from the plan's metric, plus its `coverage=`
    companion when the metric is a rate over a filtered subset. Match the plan's
    `The table` section: a BOOLEAN column for a per-case rate, a callable
    (`lambda d: d['n_ok'].sum() / d['n'].sum()`) for a rate pooled over items. A
    fraction or a count passed as a column name stops the run with
    `TypeError: Need to pass bool-like values`;
  - `guardrail = ev.Metric(..., higher_is_better=False, budget=...)` from the
    plan's guardrail. A missing guardrail is not an option: a change that acts on
    everything scores 100% on "did it act" and ships a regression;
  - `slices` - the metadata columns worth breaking the metric down by;
  - `code_version()` covering what the arm READS (prompt files, the git ref, the
    model id), so editing one invalidates that arm. Not the scorers: they key the
    scoring stage themselves, and editing one re-scores with no model calls.
  - scorers: reuse pydantic-evals before writing one - `LLMJudge`, `GEval`,
    `EqualsExpected`, the tool-call evaluators, `ConfusionMatrixEvaluator`.
- **The baseline arm** - materialize it with `ev.git_tree(ref, paths)` at the ref
  the plan names, and have `code_version()` return the RESOLVED sha
  (`git rev-parse <ref>`), not the ref string. Do not build a baseline by
  string-replacing the live files: a replacement cannot restore a section the
  change deleted, and it decays silently as the live template moves.
- **`cases.csv`** - leave the placeholder rows alone; `/oryxflow:eval-cases`
  fills them. Keep the `synthetic` column and the control row - they are schema.

Leave the `PLACEHOLDER SCAFFOLD` marker on the `CASES` line of `eval.py` - it tells
`/oryxflow:check-standards` and `/oryxflow:update-project` that this eval still
runs on placeholder cases. Delete every OTHER marker you filled.

Name any declaration the plan did not answer rather than inventing one. If the
plan has no `Measure` / `The table`, `Data` or `Running it` section, it predates
those - derive what you can, and say which gate numbers have no column behind them.

## 4. Check the imports resolve

Two probes, run FROM `evals/` with the project's own interpreter. Both must pass
before step 5 - on either failure, print the exact fix for THIS project's
environment and STOP. Do not install anything yourself.

**a. `oryxflow[evals]`** - `python -c "import oryxflow.evals"`. The fix names the
minimum version, because older releases have no `oryxflow.evals`:

- uv project (`uv.lock`, `[tool.uv]`): `uv pip install "oryxflow[evals]>=26.10.5"`
- poetry (`poetry.lock`): `poetry add "oryxflow[evals]>=26.10.5"`
- venv / conda env: `pip install "oryxflow[evals]>=26.10.5"`

Quote the extras bracket - unquoted `oryxflow[evals]` is a glob in zsh. If the
production package pins its dependencies in a subdirectory's `pyproject.toml`,
that is the environment to install into.

**b. The eval package and its production import** -
`python -c "import <name>.agent"` from `evals/`. That runs `_env.py` and the
production import together, so it proves exactly what the eval will see.

A `ModuleNotFoundError` for the production module is almost always the package not
being installed, or `_env.py` not pointing at it - not a missing dependency. Print
the fix (`pip install -e <dir holding its pyproject.toml>`, or the `_env.py` path)
and stop.

Tell the user to re-run `/oryxflow:eval-init` once it resolves: the copy and the
fill are already done, so it resumes at the smoke run.

## 5. Smoke run - 3 cases, 1 arm, 1 rep

Prove the credentials and the wiring BEFORE anyone pays for a sweep. This costs
about three API calls; say so before you run it. Run both FROM `evals/`:

1. `python run_eval_<name>.py --check` - preflight only, one call.
2. Then the smoke sweep: the three placeholder cases, ONE arm, `--repeats 1`,
   `--yes`.

A run launched from anywhere else prints a warning and builds a second cache -
stop and re-run from `evals/` if you see it.

**Read the outcome before believing it.** A credential or wiring failure must
surface as an ERROR, never as an empty result:

- every case errored, or the frame came back empty - the smoke run FAILED. Report
  the first stacktrace, say plainly that nothing was measured, and fix it or hand
  back. Never report an all-error sweep as a pass.
- a cell cached before you caught it - re-run with `--reset` after the fix (it
  discards the model calls too), or that empty cell is served forever.
- some cases errored - name how many and why. That is a finding, not noise.

Do not interpret the numbers here. Three cases cannot support a verdict.

## 6. Report

State exactly which files were CREATED and which were SKIPPED (already present) -
including whether `_env.py` was new - which declarations you filled from the plan
and which the plan left open, and the smoke run's outcome: passed, or the error
it surfaced.

Close honestly:

> 3 cases is not a measurement - run `/oryxflow:eval-cases` to get to 15-25.

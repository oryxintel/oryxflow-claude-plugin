---
description: Scaffold an eval directory from the bundled eval template (skip-existing, never overwrite), fill it from the eval plan, and prove the wiring with a 3-call smoke run.
disable-model-invocation: true
---

# Scaffold an eval from the plan

Copy the bundled eval template into `evals/<name>/` and wire it to the decisions
already recorded in that eval's plan, so the user has a runnable harness.

- Template source: `${CLAUDE_PLUGIN_ROOT}/resources/template-eval/`
- Target: `${CLAUDE_PROJECT_DIR}/evals/<name>/`
- `<name>` comes from the user's argument. With none, name it after the surface
  under test (`prompt-triage`, `summarizer`) and say which name you chose.

This command COPIES FILES. `/oryxflow:eval-plan` is the command that DECIDES -
what is measured, the guardrail, the baseline. Do not re-decide any of that here;
read it out of the plan and wire it in. Same split as the library's `preview` /
`run`.

Follow these steps exactly.

## 1. Pre-flight - there must be a plan

Read `evals/<name>/README.md`.

- **It exists.** Use it. Every declaration you write below comes from it.
- **It does not exist.** Run the `/oryxflow:eval-plan` flow INLINE - gather the
  same context and ask the same four questions (function under test, metric plus
  its coverage metric, guardrail, baseline ref). Show the resulting plan and WAIT
  for a yes. Write NOTHING - not the README, not a template file - until the user
  confirms. On confirmation, write `evals/<name>/README.md` and continue.

Never skip the plan and scaffold from your own guesses. An eval whose metric was
never argued measures whatever the scaffold happened to declare.

## 2. Copy the template (skip-existing, never overwrite)

Copy every file and subdirectory from the template source into the target,
preserving the layout (including `fixtures/` and `results/`). One hard rule:
NEVER overwrite a file that already exists in the target - skip it and remember
it for the report. That is what makes re-running this command safe on an eval the
user has already edited.

Do the copy with a single SHELL COPY COMMAND. Do NOT read the template files into
context and re-write them with the Write tool - that is slow and can corrupt
binary-ish files. Pick the copy command by PLATFORM and use it consistently - do
not improvise a different one each run:

- **Windows (the default here): `robocopy`** via the PowerShell tool:
  `robocopy "<src>" "<dst>" /E /XC /XN /XO` (the `/XC /XN /XO` flags skip files
  that already exist in the target). This is the standard path on this OS - reach
  for `robocopy` first, not `cp` / `Copy-Item`.
- macOS / Linux: `cp -rn "<src>/." "<dst>/"` (`-n` = no-clobber).

**robocopy exit codes are NOT shell errors.** robocopy returns 0-7 on SUCCESS
(1 = files copied, 0 = nothing to copy, 2/3 = extras present) and only >= 8 is a
real failure. Exit code 1 means the copy worked - do NOT treat it as an error or
retry with a different command. Only investigate when the code is >= 8.

After the copy, diff the source and target file lists to determine what was newly
created vs skipped (for the report) - again via shell (e.g. compare directory
listings), not by reading file contents.

The template contains `agent.py` (the function under test), `eval.py` (the
`TaskEval`), `run_eval.py` (the CLI entry point), `cases.csv` (a header plus
three placeholder rows, one of them a control), and the `fixtures/` and
`results/` directories. `README.md` is NOT in the template - the plan wrote it.

## 3. Fill the template from the plan

Edit the COPIED files, never the template. Read the plan's six answers and wire
each one:

- **`agent.py`** - import the function under test from PRODUCTION code at the
  entry point the plan names. Import it; do not copy it, do not re-render its
  prompt here. A second copy of the instructions inside `evals/` drifts from the
  live ones and then measures nothing. Keep the template's comment saying so.
- **`eval.py`** - declare:
  - the arm parameters (the axis the plan compares, e.g. a prompt version), one
    oryxflow Parameter each;
  - `metric = ev.Metric(...)` from the plan's metric, plus its `coverage=`
    companion when the metric is a rate over a filtered subset - a quality rate
    is read after coverage, never alone, because a subset is gameable by
    shrinking it. Match the plan's `The table` section: a BOOLEAN column for a
    per-case rate, a callable (`lambda d: d['n_ok'].sum() / d['n'].sum()`) for a
    rate pooled over items inside the output. A fraction or a count passed as a
    column name stops the run with `TypeError: Need to pass bool-like values`;
  - `guardrail = ev.Metric(..., higher_is_better=False, budget=...)` from the
    plan's guardrail. A missing guardrail is not an option: a change that acts on
    everything scores 100% on "did it act" and ships a regression;
  - `slices` - the metadata columns worth breaking the metric down by;
  - `code_version()` covering the prompt/template files the arms actually read,
    so editing one invalidates that arm instead of serving a stale cell.
- **The baseline arm** - materialize it with `ev.git_tree(ref, paths)` at the ref
  the plan names, and have `code_version()` return the RESOLVED sha
  (`git rev-parse <ref>`), not the ref string. Do not build a baseline by
  string-replacing the live files: a replacement cannot restore a section the
  change deleted, and it decays silently as the live template moves.
- **`cases.csv`** - leave the placeholder rows alone; `/oryxflow:eval-cases`
  fills them. Keep the `synthetic` column and the control row - they are schema,
  not examples.

Leave the `PLACEHOLDER SCAFFOLD` marker in `eval.py`. It is what tells
`/oryxflow:check-standards` and `/oryxflow:update-project` that this eval still
runs on placeholder cases; a real case set is what earns its removal.

- **`agent.py` return value** - return exactly the columns the plan's `The table`
  section lists. Every number the verdict prints is one of them, so a gate the
  columns cannot produce is a finding to report now, not at the first run.

Name any declaration the plan did not answer rather than inventing one. If the
plan has no `Measure`/`The table`, `Data` or `Running it` section, it predates those -
derive what you can, and say which gate numbers have no column behind them.

## 4. Check the imports resolve

Two probes against the project's own interpreter. Both must pass before step 5 -
on either failure, print the exact command for THIS project's environment and
STOP. Do not install anything yourself, and do not run the smoke run.

**a. `oryxflow[evals]`** - `python -c "import oryxflow.evals"`.

- uv project (`uv.lock`, `[tool.uv]`): `uv pip install "oryxflow[evals]"`
- poetry (`poetry.lock`): `poetry add "oryxflow[evals]"`
- venv / conda env: `pip install "oryxflow[evals]"`

Quote the extras bracket - unquoted `oryxflow[evals]` is a glob in zsh.

**b. The entry point the plan names** - `python -c "import <module>"` for the
production module `agent.py` imports, run from the eval directory so it proves
what the eval itself will see.

A `ModuleNotFoundError` here is almost always the project not being installed,
not a missing dependency: the eval imports production code, and a project whose
modules sit at the repo root is importable only from the repo root until it is.
Print the fix and stop:

- uv project: `uv pip install -e .`
- poetry (`poetry.lock`): `poetry install`
- venv / conda env: `pip install -e .`

Run it from the project root, not the eval directory.

If the project has no `pyproject.toml` at all, say so - `/oryxflow:init-project`
ships one, and an older scaffold predates it.

Tell the user to re-run `/oryxflow:eval-init` once it installs: the copy and the
fill are already done, so it resumes at the smoke run.

## 5. Smoke run - 3 cases, 1 arm, 1 rep

Prove the credentials and the wiring BEFORE anyone pays for a sweep. This costs
about three API calls; say so before you run it.

1. `python run_eval.py --check` - preflight only, one call. It answers "do my
   credentials work" for the price of one case.
2. Then the smoke sweep: the three placeholder cases, ONE arm, `--repeats 1`,
   `--yes`.

Run it from the working directory the template expects, and confirm the relative
paths (`cases.csv`, `fixtures/`) resolve from there. A harness launched from the
wrong directory is an observed failure: every case raised, the sweep completed,
and an EMPTY result cached as if it were a measurement.

**Read the outcome before believing it.** A credential or wiring failure must
surface as an ERROR, never as an empty result:

- every case errored, or the frame came back empty - the smoke run FAILED. Report
  the first stacktrace, say plainly that nothing was measured, and fix it or hand
  back. Never report an all-error sweep as a pass.
- a cell cached before you caught it - re-run with `--reset` after the fix, or
  that empty cell is served forever.
- some cases errored - name how many and why. That is a finding, not noise.

Do not interpret the numbers here. Three cases cannot support a verdict.

## 6. Report

State exactly which files were CREATED and which were SKIPPED (already present),
which declarations you filled from the plan and which the plan left open, and the
smoke run's outcome - passed, or the error it surfaced.

Close honestly:

> 3 cases is not a measurement - run `/oryxflow:eval-cases` to get to 15-25.

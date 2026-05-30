---
description: Scaffold a new d6tflow project into the current directory from the bundled minimal template (skip-existing, never overwrite).
---

# Scaffold a new d6tflow project

Copy the bundled minimal d6tflow template into the user's project directory so they
have a runnable starting point.

- Template source: `${CLAUDE_PLUGIN_ROOT}/resources/template-minimal/`
- Target: the current project directory `${CLAUDE_PROJECT_DIR}` (where Claude Code
  was launched).

Follow these steps exactly.

## 1. Pre-flight - do not clobber an existing project

Inspect the target directory. If it ALREADY looks like a d6tflow project - any of
`tasks.py`, `flow.py`, or `CLAUDE.md` exist - STOP. Do not copy anything yet.
Report what you found and ask the user whether they want to (a) scaffold only the
missing files, or (b) cancel. Proceed only on their answer.

If the directory has no d6tflow files, continue.

## 2. Copy the template (skip-existing, never overwrite)

Copy every file and subdirectory from the template source into the target,
preserving the layout (including `docs/`). One hard rule: NEVER overwrite a file
that already exists in the target - skip it and remember it for the report.

Do the copy with a single SHELL COPY COMMAND. Do NOT read the template files into
context and re-write them with the Write tool - that is slow and can corrupt
binary-ish files like `visualize.ipynb`. Use the platform-appropriate, no-clobber
copy and let the tool handle the recursion and skipping:

- Windows (PowerShell): `robocopy "<src>" "<dst>" /E /XC /XN /XO` (the `/XC /XN
  /XO` flags skip files that already exist in the target).
- macOS / Linux: `cp -rn "<src>/." "<dst>/"` (`-n` = no-clobber).

After the copy, diff the source and target file lists to determine what was newly
created vs skipped (for the report) - again via shell (e.g. compare directory
listings), not by reading file contents.

The template contains the project wiring (`cfg.py`, `flow_params.py`, `flow.py`,
`run.py`, `tasks.py`, `visualize.py`, `visualize.ipynb`), `CLAUDE.md`,
`.gitignore`, `.creds.yaml.example`, and `docs/d6tflow-data.md`. `tasks.py` and
`flow_params.py` ship with a `PLACEHOLDER SCAFFOLD` marker (and `tasks.py`'s
module + task docstrings are placeholders); `docs/d6tflow-data.md` ships with a
`PLACEHOLDER` marker on line 1. Those markers are intentional - leave them; they
are replaced when the real pipeline and data findings are written. (Pipeline
documentation lives in the code's docstrings, not a separate doc.)

## 3. Create the data directory

Ensure an empty `data/` exists in the target (it is gitignored; d6tflow writes
per-task parquet outputs there).

## 4. Report

Tell the user exactly which files were CREATED and which were SKIPPED (already
present). If `CLAUDE.md` was skipped, note the template version lives at
`${CLAUDE_PLUGIN_ROOT}/resources/template-minimal/CLAUDE.md` for them to diff.

Finish with the next steps: the scaffold runs as-is (`python run.py`) but does no
real work yet; replace the `PLACEHOLDER SCAFFOLD` tasks in `tasks.py` with the real
pipeline (documenting them via the module + task docstrings), and fill
`docs/d6tflow-data.md` as data findings accumulate.

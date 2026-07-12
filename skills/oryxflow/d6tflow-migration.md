# Migrating a d6tflow-era project to oryxflow

The library was renamed `d6tflow` -> `oryxflow`; the public API kept its shape
(same `tasks.TaskPqPandas`, `@requires`, `BoolParameter`, `Workflow`, `settings`,
`set_dir` - only the top-level package name changed). So migrating an old project
is essentially a `d6tflow` -> `oryxflow` token rename, not an API port.

Loaded ON DEMAND, only when the user asks to migrate a d6tflow project (e.g.
"migrate from d6tflow to oryxflow using the plugin's d6tflow migration
instructions"). It does NOT auto-trigger. This is a one-time, one-way migration;
work PLAN-then-APPLY - author the rename plan, show it, and edit only on the
user's go-ahead. For the general library reference see [reference.md](reference.md);
for the essentials see [SKILL.md](SKILL.md).

> Not to be confused with restructuring a messy data-science project (notebooks /
> linear scripts) into an oryxflow pipeline - that is `/oryxflow:migrate`. This doc
> only covers renaming an already-oryxflow-shaped project that still uses the old
> `d6tflow` name.

## 1. Detect

Grep the project for the whole-word token `d6tflow` across ALL text files -
Python source, deps files, docs, notebooks (`*.ipynb`), and rendered reports
(`*.html`). No hits -> there is nothing to rename; if the user's project is
instead an old oryxflow scaffold that has drifted, point them at
`/oryxflow:update-project` and STOP. Otherwise collect the matching FILE LIST -
it is both your migration surface and the exact scope for step 4's substitution.

## 2. Library check (a user decision - never auto-install)

The rename assumes the new package is importable. Confirm it and check the
version BEFORE editing:

- Is `oryxflow` installed? (`python -c "import oryxflow, sys;
  print(oryxflow.__version__)"`).
- Compare that version to the compatibility floor this skill assumes (the
  `oryxflow >= X` value in [SKILL.md](SKILL.md)'s "Compatibility" line - read it
  there, do not hardcode a second copy).

If `oryxflow` is missing, or older than the floor, present `pip install oryxflow`
(or an upgrade) as an EXPLICIT user choice and let them run it - do not install
or upgrade on their behalf. If they decline, you can still stage the rename, but
warn that `python run.py` will fail until the package is present.

## 3. Build the rename plan (the mechanical core)

Whole-word `d6tflow` -> `oryxflow`. Word boundaries matter - do not rewrite an
unrelated substring. The surface:

- **Python** (`*.py`): imports, decorators, base classes, parameter types,
  settings, and workflow calls all just swap the prefix - `import d6tflow` ->
  `import oryxflow`, `@d6tflow.requires` -> `@oryxflow.requires`,
  `d6tflow.tasks.TaskPqPandas` -> `oryxflow.tasks.TaskPqPandas`,
  `d6tflow.BoolParameter` -> `oryxflow.BoolParameter`, `d6tflow.settings.*`,
  `d6tflow.set_dir(...)`, `d6tflow.Workflow(...)`, `d6tflow.enable_logging()`.
- **Dependencies**: `d6tflow` -> `oryxflow` in `requirements.txt`,
  `pyproject.toml`, `setup.py`, `environment.yml` (whichever exist).
- **Data doc**: rename `docs/d6tflow-data.md` -> `docs/oryxflow-data.md` and swap
  the token inside it.
- **Floor stamp**: if `CLAUDE.md` has no `<!-- oryxflow-floor: VERSION -->`
  stamp, note that `/oryxflow:update-project` will add it (see step 5); do not
  hand-invent a version.
- **Template URLs**: any `d6t/d6tflow-template` link -> the current oryxflow
  template (the plugin's bundled scaffold).
- **Notebooks and reports**: `*.ipynb` (the token lives in code-cell source) and
  any rendered `reports/render/*.html` - swap the token in place. Often absent (a
  `--no-input` report strips code cells), but include any that grep found.

FLAG, do not auto-rewrite, anything that does NOT map 1:1 - e.g. a very old
project on a deprecated idiom (module-level `d6tflow.run(...)` instead of the
`Workflow` object, a removed helper). Report those for manual review rather than
guessing a rewrite; a clean rebrand should not need them, so a mismatch is a
signal, not a token to blindly swap.

## 4. Propose, then apply as ONE scripted substitution

Present the plan first - a per-file summary (files touched, hit count, the
data-doc rename, anything flagged for manual review). Do NOT edit yet.

On confirmation, apply the rename as a SINGLE scripted pass over exactly the
files detection found - do NOT fan it out into per-file `Edit` calls. That is
slow, it is easy to miss a hit, and it is the wrong tool: `d6tflow` -> `oryxflow`
is a whole-word swap of a quote-free ASCII token, so a word-boundary substitution
is safe and complete:

    perl -i -pe 's/\bd6tflow\b/oryxflow/g' <the detected files>

(GNU `sed -E -i` takes the same `s/\bd6tflow\b/oryxflow/g`; PowerShell:
`(Get-Content $f) -replace '\bd6tflow\b','oryxflow' | Set-Content $f`.) The `\b`
boundaries turn `d6tflow-template` into `oryxflow-template` while leaving an
unrelated `d6tflow_custom` identifier alone - that mismatch is a FLAG case
(step 3), not a token to swap.

INCLUDE `.ipynb` / `.html` in this pass. This is the one time to rewrite a
notebook as TEXT rather than via `NotebookEdit`: the house rule against
hand-writing nbformat JSON is about AUTHORING cells, and swapping an identical
quote-free token everywhere cannot corrupt the JSON (NotebookEdit also can't do a
project-wide find-replace). So the script rewrites the notebooks too.

Then do the two things a substitution can't:
- RENAME the data-doc FILE: `docs/d6tflow-data.md` -> `docs/oryxflow-data.md`
  (`git mv` if tracked) - its internal token was already swapped by the pass.
- RE-GREP for `d6tflow` and confirm zero hits remain except the ones you FLAGGED.
  A survivor is a boundary/edge case the regex skipped - resolve it by hand, do
  not loosen the pattern.

## 5. Smoke-test and hand off

- Run `python run.py` as a cheap regression smoke test (this scaffold has no
  version pin and imports oryxflow across several files, so a package switch can
  silently change behavior). If it fails on a symbol, diagnose via reference.md
  "Diagnosing a regression / version bump".
- If the project is a git repo (`.git` present), OFFER to commit the rename - a
  clean whole-word swap is an ideal standalone commit. Confirm first, and ask
  whether to commit on the CURRENT branch or a NEW one; on their go-ahead, make
  the commit (create the branch first if new - e.g.
  `git switch -c rename-d6tflow-oryxflow`, then `git commit -am "Rename d6tflow
  -> oryxflow"`). Attempt it, do not just suggest and stop. Don't push unless
  asked; the follow-ups below are separate later commits.
- Point the user at the follow-ups that cover the non-rename drift:
  `/oryxflow:update-project` (reconcile the scaffold floor and set the floor
  stamp) and `/oryxflow:check-standards` (names, style, docstrings).

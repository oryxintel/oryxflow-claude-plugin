# d6tflow plugin

A Claude Code plugin for building highly effective data science workflows with
[d6tflow](https://github.com/d6t/d6tflow): chain together complex,
parameterized data flows with dependencies and caching, and rerun them
intelligently after code or parameter changes - so you build better models
faster.

It ships one skill, `d6tflow`, that activates when you work in a d6tflow project
- editing `tasks.py` / `flow.py` / `run.py` / `cfg.py` / `flow_params.py`, adding
or modifying pipeline tasks, running workflows, or analyzing outputs.

## Quickstart

Already installed? Two things to know:

- Scaffold a new project: run `/d6tflow:init-project` in an empty directory.
- Put `data/` under Git LFS: run `/d6tflow:init-gitlfs` in the project.
- Use it: just start working in a d6tflow project and the skill auto-activates,
  or invoke it manually with `/d6tflow:d6tflow`.

New here? Start with [Install](#install).

## Install

This repo is its own marketplace, so it can be installed directly.

### From GitHub

```
/plugin marketplace add https://github.com/d6t/d6tflow-claude-plugin.git
/plugin install d6tflow@d6tflow
```

The full HTTPS URL works for everyone on a public repo with no auth setup.

The `owner/repo` shorthand also works, but only if your git is set up to reach
GitHub over HTTPS or you have a `github.com` SSH key loaded - on some SSH setups
it fails with "Permission denied (publickey)". Prefer the HTTPS URL above if
unsure.

```
/plugin marketplace add d6t/d6tflow-claude-plugin
/plugin install d6tflow@d6tflow
```

### From a local clone

```
/plugin marketplace add /path/to/d6tflow-claude-plugin
/plugin marketplace add D:\OneDrive\dev\d6tlib\d6tflow-claude-plugin   # e.g.
/plugin install d6tflow@d6tflow
```

To pull a newer version later: `/plugin marketplace update d6tflow`.

## Start a new project

In an empty directory, scaffold a runnable d6tflow project:

```
/d6tflow:init-project
```

This copies a minimal template into the current directory - the project wiring
(`tasks.py`, `cfg.py`, `flow.py`, `run.py`, `flow_params.py`, `visualize.py`),
a project `CLAUDE.md`, a `.gitignore` / `.creds.yaml.example`, and a
`docs/d6tflow-data.md` skeleton for data findings. It never overwrites existing
files. `python run.py` works immediately; replace the `PLACEHOLDER SCAFFOLD`
tasks with your real pipeline (documented via task docstrings) and fill
`docs/d6tflow-data.md` as you learn about the data.

## Version your data with Git LFS

d6tflow caches per-task outputs under `data/` (parquet, csv, json); the scaffold
gitignores them. To version them instead, run:

```
/d6tflow:init-gitlfs
```

It checks git-lfs is installed and hooked into git (guiding you through
`winget install GitHub.GitLFS` / `brew install git-lfs` if not), initializes a
git repo on `main` if needed, un-ignores the data files in `.gitignore`, runs
`git lfs track "data/**"` and `git lfs track "reports/render/**"`, and commits the
LFS config. Committing the actual data is left to you as a follow-up.

## Using the skill

Once installed, the skill is always available - there is nothing to turn on per
session. It auto-activates when you work in a d6tflow project: editing the
pipeline files, adding or modifying tasks, running flows, or analyzing outputs.
You can also invoke it explicitly any time with `/d6tflow:d6tflow`, or pass the
deep-dive argument with `/d6tflow:d6tflow explore`.

Scaffolding a new project and setting up Git LFS are separate, manually-triggered
commands - `/d6tflow:init-project` and `/d6tflow:init-gitlfs` - they are not
auto-invoked, since they write files and run git.

Things you can ask, in plain language:

Build the pipeline:
- "load the `<X>` data" - creates an output-named loader task (e.g. `DataOEWS`)
- "add a task `<Name>` that takes `<Upstream>`'s output and ..." - the common
  case: a new task wired to an upstream with `@d6tflow.requires(<Upstream>)`
- "create a task `<Name>` that loads `<source>`" - a root task (no dependency)
- "add a task `<Name>` that depends on `<A>` and `<B>`" - multiple inputs
- "save `<field>` in `<Task>`" / "add (or drop) a column in `<Task>`" - edits the
  task; reset cascades downstream on re-run (removing a column, fix its readers)
- "make `<Task>` depend on `<Other>`" / "set `<Task>` as the final task"
- "add a parameter `<name>` to `<Task>`" / "change `<param>` to `<value>`"

Run and inspect:
- "run the flow" - runs `python run.py`
- "preview the flow" / "what will run?" - shows `flow.preview()`
- "update `<Task>` to ..." then "run the flow" - after a code edit the skill
  resets the task before running (an unreset edit is silently skipped)
- "re-run `<Task>`" / "reset `<Task>`" - recompute it; reset cascades downstream
- "load the output of `<Task>`" / "plot the results"

Understand:
- "what does this pipeline do?" - summarize the flow
- "explore the data" - opt-in deep dive that profiles `data/` and writes findings

For more on d6tflow itself, see [Resources](#resources).

## Developing the plugin

Iterate without installing - load the plugin directly for one session:

```
claude --plugin-dir /path/to/d6tflow-claude-plugin
claude --plugin-dir D:\OneDrive\dev\d6tlib\d6tflow-claude-plugin   # e.g.
```

After editing any plugin file (`SKILL.md`, `reference.md`, `commands/*`,
`resources/*`), run `/reload-plugins` to pick up changes - the files are read
live from disk, so no version bump or reinstall is needed. Validate the
manifests with `/plugin validate .` (or `claude plugin validate .`).

**Gotcha: `--plugin-dir` and an install behave differently.** `/reload-plugins`
only works in `--plugin-dir` mode, where files are read live from disk. If you
instead *installed* the plugin (see [Install](#install)) - even from a local
clone - your edits do NOT show up via reload or a restart. An install resolves a
fixed `version`, so changes only propagate after you release them (bump `version`
+ commit, below) and the owner runs `/plugin marketplace update d6tflow`. That is
the right behavior for consumers, but it makes an install a poor way to iterate.

**Suggested setup: use both, for their two different jobs.**

- *Developing the plugin* (editing `SKILL.md`, `reference.md`, etc.): launch with
  `claude --plugin-dir <repo>` and `/reload-plugins` after each edit. Instant
  feedback, no version bump.
- *Using the plugin* in your real d6tflow projects: `/plugin install` it once
  (see [Install](#install)) so it is always on without passing any flag.

Do not do both in the same session - `--plugin-dir` plus an active install loads
the skill twice and the two copies can drift. Keep `--plugin-dir` for this repo
and the install for everywhere else.

### Releasing

The top section of `docs/CHANGELOG.md` is the current working version, and its
version string matches `.claude-plugin/plugin.json`. There is no "Unreleased"
bucket - add changelog bullets to that top section as you work.

1. Add a changelog bullet for each change as you make it.
2. To cut a release for consumers, set `version` in `.claude-plugin/plugin.json`
   to the release date in `YY.M.D` format (e.g. `26.5.30`; append `.N` for
   multiple releases in a day) and give the top changelog section the matching
   heading.
3. Commit (and push, if consumers install from git).

Installed copies pick up the change when their owner runs
`/plugin marketplace update d6tflow`. The version bump is the signal that there
is something new - skip it and the update may not register. (Git installs with
no pinned version fall back to the commit SHA, so a new commit counts as new;
but since we set an explicit version, it must be bumped.)

## Contents

```
d6tflow-claude-plugin/
|-- .claude-plugin/
|   |-- plugin.json        # plugin manifest
|   `-- marketplace.json   # lets this repo act as its own marketplace
|-- commands/
|   |-- init-project.md    # /d6tflow:init-project - scaffold a new project
|   `-- init-gitlfs.md     # /d6tflow:init-gitlfs - put data/ under Git LFS
|-- resources/
|   `-- template-minimal/  # the files init-project copies into a new project
`-- skills/
    `-- d6tflow/
        |-- SKILL.md       # skill entry point (loaded into context)
        |-- reference.md   # full library reference, loaded on demand
        |-- conventions.md # house conventions (layout, code-org, naming), on demand
        `-- ml-patterns.md # ML pipeline task templates, loaded on demand
```

## Resources

Learn more about d6tflow itself (the underlying library this plugin helps you
work with):

- d6tflow documentation: https://d6tflow.readthedocs.io/
- d6tflow source: https://github.com/d6t/d6tflow
- Maintainer: https://databolt.tech

This plugin's own repository and issue tracker:
https://github.com/d6t/d6tflow-claude-plugin

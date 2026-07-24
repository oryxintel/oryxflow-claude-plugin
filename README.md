# oryxflow — the Claude Code plugin for reproducible AI data analysis

The official [oryxflow](https://github.com/oryxintel/oryxflow) plugin for **Claude
Code** - a **skill plus slash commands** (not an MCP server) that teach the agent to
build your data analysis as a cached, reproducible pipeline. Chain together complex,
parameterized data flows with dependencies and caching, and rerun them intelligently
after code or parameter changes - so AI-written data analysis is faster, cheaper, and
more trustworthy: reproducible by default, and you build better models faster.

It ships one skill, `oryxflow`, that activates when you work in a oryxflow project
- editing `tasks.py` / `flow.py` / `run.py` / `cfg.py` / `flow_params.py`, adding
or modifying pipeline tasks, running workflows, or analyzing outputs.

## Quickstart

Already installed? Two things to know:

- Scaffold a new project: run `/oryxflow:init-project` in an empty directory.
- Put `data/` under Git LFS: run `/oryxflow:init-gitlfs` in the project.
- Update an old project to the latest scaffold: run `/oryxflow:update-project`.
- Check code against the house standards: run `/oryxflow:check-standards`.
- Restructure a messy project (notebooks / linear scripts) into a pipeline: run
  `/oryxflow:migrate` (scaffold first with `/oryxflow:init-project` if needed).
- Migrate an old `d6tflow` project to `oryxflow`: with the skill active, just ask
  (e.g. "migrate from d6tflow to oryxflow using the plugin's d6tflow migration
  instructions"). It is a guided rename, not a slash command.
- Use it: just start working in a oryxflow project and the skill auto-activates,
  or invoke it manually with `/oryxflow:oryxflow`.

New here? Start with [Install](#install).

## Install

This repo is its own marketplace, so it can be installed directly.

### From GitHub

```
/plugin marketplace add https://github.com/oryxintel/oryxflow-claude-plugin.git
/plugin install oryxflow@oryxflow
```

The full HTTPS URL works for everyone on a public repo with no auth setup.

The `owner/repo` shorthand also works, but only if your git is set up to reach
GitHub over HTTPS or you have a `github.com` SSH key loaded - on some SSH setups
it fails with "Permission denied (publickey)". Prefer the HTTPS URL above if
unsure.

```
/plugin marketplace add oryxintel/oryxflow-claude-plugin
/plugin install oryxflow@oryxflow
```

### From a local clone

```
/plugin marketplace add /path/to/oryxflow-claude-plugin
/plugin marketplace add D:\OneDrive\dev\oryxlib\oryxflow-claude-plugin   # e.g.
/plugin install oryxflow@oryxflow
```

To pull a newer version later: `/plugin marketplace update oryxflow`. Updates are
pull-based - there is no push notification, so run this periodically to pick up
new releases (the [CHANGELOG](docs/CHANGELOG.md) lists what changed).

## Start a new project

In an empty directory, scaffold a runnable oryxflow project:

```
/oryxflow:init-project
```

This copies a minimal template into the current directory - the project wiring
(`tasks.py`, `cfg.py`, `flow.py`, `run.py`, `flow_params.py`, `visualize.py`),
a project `CLAUDE.md`, a `.gitignore` / `.creds.yaml.example`, and a
`docs/oryxflow-data.md` skeleton for data findings. It never overwrites existing
files. `python run.py` works immediately; replace the `PLACEHOLDER SCAFFOLD`
tasks with your real pipeline (documented via task docstrings) and fill
`docs/oryxflow-data.md` as you learn about the data.

## Version your data with Git LFS

oryxflow caches per-task outputs under `data/` (parquet, csv, json); the scaffold
gitignores them. To version them instead, run:

```
/oryxflow:init-gitlfs
```

It checks git-lfs is installed and hooked into git (guiding you through
`winget install GitHub.GitLFS` / `brew install git-lfs` if not), initializes a
git repo on `main` if needed, un-ignores the data files in `.gitignore`, runs
`git lfs track "data/**"` and `git lfs track "reports/render/**"`, and commits the
LFS config. Committing the actual data is left to you as a follow-up.

## Update an existing project

A project scaffolded a while ago can fall behind the latest template (newer
`CLAUDE.md` conventions, an older `.gitignore`, a stale report template). To bring
its scaffold floor up to date without touching your pipeline:

```
/oryxflow:update-project
```

It diffs the template against your project, proposes a per-file migration plan,
and applies only what you approve - never overwriting your `tasks.py` / wiring or
your data doc's real content. The skill also points you here on its own when it
notices a project whose floor predates the current scaffold.

## Using the skill

Once installed, the skill is always available - there is nothing to turn on per
session. It auto-activates when you work in a oryxflow project: editing the
pipeline files, adding or modifying tasks, running flows, or analyzing outputs.
You can also invoke it explicitly any time with `/oryxflow:oryxflow`, or pass the
deep-dive argument with `/oryxflow:oryxflow explore`.

Scaffolding a new project, setting up Git LFS, updating an old project's floor,
checking code against the standards, and restructuring a messy project into a
pipeline are separate, manually-triggered commands - `/oryxflow:init-project`,
`/oryxflow:init-gitlfs`, `/oryxflow:update-project`, `/oryxflow:check-standards`,
and `/oryxflow:migrate` - they are not auto-invoked, since they write files, run
git, or edit your code.

Things you can ask, in plain language:

Build the pipeline:
- "load the `<X>` data" - creates an output-named loader task (e.g. `DataOEWS`)
- "add a task `<Name>` that takes `<Upstream>`'s output and ..." - the common
  case: a new task wired to an upstream with `@oryxflow.requires(<Upstream>)`
- "create a task `<Name>` that loads `<source>`" - a root task (no dependency)
- "add a task `<Name>` that depends on `<A>` and `<B>`" - multiple inputs
- "save `<field>` in `<Task>`" / "add (or drop) a column in `<Task>`" - edits the
  task; auto invalidation reruns it and its downstream (removing a column, fix its readers)
- "make `<Task>` depend on `<Other>`" / "set `<Task>` as the final task"
- "add a parameter `<name>` to `<Task>`" / "change `<param>` to `<value>`"

Run and inspect:
- "run the flow" - runs `python run.py`
- "preview the flow" / "what will run?" - shows `flow.preview()`
- "update `<Task>` to ..." then "run the flow" - after a code edit auto
  invalidation reruns the task; the skill verifies it actually reran
- "re-run `<Task>`" / "reset `<Task>`" - recompute it; reset cascades downstream
- "load the output of `<Task>`" / "plot the results"

Understand:
- "what does this pipeline do?" - summarize the flow
- "explore the data" - opt-in deep dive that profiles `data/` and writes findings

For more on oryxflow itself, see [Resources](#resources).

## Best practices

The conventions the skill applies are the same files it loads - one source, two
readers (you and the coding agent):

- [conventions.md](skills/oryxflow/conventions.md) - house layout, code
  organization (grouping `eda/` / `utils/` / `viz/` by subject), and naming
  columns / tasks / variables.
- [ml-patterns.md](skills/oryxflow/ml-patterns.md) - ML pipeline task templates
  (feature engineering, model training, SHAP, expanding-window backtests) and the
  productionizing lifecycle.

## What's new

The [CHANGELOG](docs/CHANGELOG.md) is the human record of what changed in each
release. Updates are pull-based - there is no push notification. You learn there
is something new only by running:

```
/plugin marketplace update oryxflow
```

The `version` bump in `plugin.json` is the machine signal that a release is
available; the changelog is the readable record of what it contains. Run the
update periodically to pick up new releases.

## Developing the plugin

Iterate without installing - load the plugin directly for one session:

```
claude --plugin-dir /path/to/oryxflow-claude-plugin
claude --plugin-dir D:\OneDrive\dev\oryxlib\oryxflow-claude-plugin   # e.g.
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
+ commit, below) and the owner runs `/plugin marketplace update oryxflow`. That is
the right behavior for consumers, but it makes an install a poor way to iterate.

**Suggested setup: use both, for their two different jobs.**

- *Developing the plugin* (editing `SKILL.md`, `reference.md`, etc.): launch with
  `claude --plugin-dir <repo>` and `/reload-plugins` after each edit. Instant
  feedback, no version bump.
- *Using the plugin* in your real oryxflow projects: `/plugin install` it once
  (see [Install](#install)) so it is always on without passing any flag.

Do not do both in the same session - `--plugin-dir` plus an active install loads
the skill twice and the two copies can drift. Keep `--plugin-dir` for this repo
and the install for everywhere else.

### Releasing

Publishing is pull-based and version-gated: `.claude-plugin/plugin.json` sets an
explicit `version`, and a consumer's `/plugin marketplace update oryxflow` only
picks up a change when that string CHANGES. Commits between bumps are invisible to
consumers, so you work in the open on `main` and gate what ships behind the bump.

While iterating, add changelog bullets under the top `## [Unreleased]` heading in
`docs/CHANGELOG.md` (`### Added` / `### Changed` / `### Removed`) and leave
`plugin.json` at the last released version - nothing ships while you work.

To cut a release:

1. Rename `## [Unreleased]` to `## [YY.M.D] - YYYY-MM-DD` with today's date (no
   zero-padding; append `.N` for a second release the same day), set `version` in
   `.claude-plugin/plugin.json` to the SAME string, and add a fresh empty
   `## [Unreleased]` back on top.
2. Commit (and push, if consumers install from git).

Installed copies pick up the release when their owner runs
`/plugin marketplace update oryxflow`. The version bump is the signal that there is
something new - skip it and the update may not register. (Git installs with no
pinned version fall back to the commit SHA, so a new commit counts as new; but
since we set an explicit version, it must be bumped.) See `CLAUDE.md` "Release" for
the full procedure, including the separate scaffold floor baseline.

## Contents

```
oryxflow-claude-plugin/
|-- .claude-plugin/
|   |-- plugin.json        # plugin manifest
|   `-- marketplace.json   # lets this repo act as its own marketplace
|-- commands/
|   |-- init-project.md    # /oryxflow:init-project - scaffold a new project
|   |-- init-gitlfs.md     # /oryxflow:init-gitlfs - put data/ under Git LFS
|   |-- update-project.md  # /oryxflow:update-project - update an old project's floor
|   |-- check-standards.md # /oryxflow:check-standards - check names, style, docstrings
|   `-- migrate.md         # /oryxflow:migrate - restructure a messy project into a pipeline
|-- resources/
|   `-- template-minimal/  # the files init-project copies into a new project
`-- skills/
    `-- oryxflow/
        |-- SKILL.md       # skill entry point (loaded into context)
        |-- reference.md   # full library reference, loaded on demand
        |-- conventions.md # house conventions (layout, code-org, naming), on demand
        `-- ml-patterns.md # ML pipeline task templates, loaded on demand
```

## Resources

Learn more about oryxflow itself (the underlying library this plugin helps you
work with):

- oryxflow documentation: https://docs.oryxflow.dev/
- Claude Code for data science: https://docs.oryxflow.dev/docs/claude-code-for-data-science/
- oryxflow source: https://github.com/oryxintel/oryxflow
- Maintainer: https://oryxintel.com

This plugin's own repository and issue tracker:
https://github.com/oryxintel/oryxflow-claude-plugin

# d6tflow plugin

A Claude Code plugin for building and working with
[d6tflow](https://github.com/d6t/d6tflow) data-science pipelines (Luigi-based:
tasks, dependencies, parameters, caching, reproducible workflows).

It ships one skill, `d6tflow`, that activates when you work in a d6tflow project
- editing `tasks.py` / `flow.py` / `run.py` / `cfg.py` / `flow_params.py`, adding
or modifying pipeline tasks, running workflows, or analyzing outputs.

## Contents

```
d6tflow-plugin/
|-- .claude-plugin/
|   |-- plugin.json        # plugin manifest
|   `-- marketplace.json   # lets this repo act as its own marketplace
`-- skills/
    `-- d6tflow/
        |-- SKILL.md       # skill entry point (loaded into context)
        `-- reference.md   # full reference, loaded on demand
```

## Install

This repo is its own marketplace, so it can be installed directly.

### From git (GitHub / GitLab / etc.)

```
/plugin marketplace add <owner>/<repo>
/plugin install d6tflow@d6tflow
```

Or with a full git URL:

```
/plugin marketplace add https://your.git.host/path/d6tflow-plugin.git
/plugin install d6tflow@d6tflow
```

### From a local clone

```
/plugin marketplace add D:\OneDrive\dev\d6tlib\d6tflow-plugin
/plugin install d6tflow@d6tflow
```

Once installed, invoke the skill manually with `/d6tflow:d6tflow`, or let Claude
auto-activate it when you work in a d6tflow project.

## Local development

Iterate without installing - load the plugin directly for one session:

```
claude --plugin-dir D:\OneDrive\dev\d6tlib\d6tflow-plugin
```

After editing `SKILL.md` / `reference.md`, run `/reload-plugins` to pick up
changes. Validate the manifests with `/plugin validate .` (or
`claude plugin validate .`).

## Releasing

Bump `version` in `.claude-plugin/plugin.json` and commit. Installs that track
this repo pick up the new version on `/plugin marketplace update d6tflow`.

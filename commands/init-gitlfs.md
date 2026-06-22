---
description: Initialize Git LFS in the current d6tflow project - check the binary is installed and hooked into git, ensure a git repo on main, un-ignore the data files, track data/** with LFS, and commit .gitattributes.
disable-model-invocation: true
---

# Initialize Git LFS for a d6tflow project

d6tflow writes large per-task outputs under `data/` (parquet, csv, json, ...).
This command puts them under Git LFS so the project can be versioned without
bloating git history. Target directory: `${CLAUDE_PROJECT_DIR}`.

Run the steps in order. Stop and report if a precondition fails.

## 1. Pre-flight - git-lfs installed AND hooked into git

These are two separate checks; do both.

- `git lfs version` - confirms the binary is on the machine. If it errors
  (`'lfs' is not a git command`, or git itself is missing), STOP, tell the user to
  install it, and have them re-run this command:
  - Windows: `winget install GitHub.GitLFS` (or `choco install git-lfs`)
  - macOS: `brew install git-lfs`
  - Linux: the distro `git-lfs` package
- `git config --get filter.lfs.clean` - confirms `git lfs install` has registered
  LFS's filters into the git config. If it prints nothing, run `git lfs install`
  once (idempotent).

## 2. Ensure a git repo on `main` (not `master`)

- `git rev-parse --is-inside-work-tree` - if it errors, this dir is not a repo:
  run `git init -b main` to initialize with `main` as the default branch.
  (If the installed git predates `-b`, fall back to `git init` then
  `git branch -m main`.)
- If it IS already a repo, leave the existing branch alone.

## 3. Un-ignore the data files in `.gitignore`

The template `.gitignore` ignores data files so a fresh project stays clean; LFS
needs them tracked instead. The data-file block is delimited by the marker lines
`# <data files>` and `# </data files>`. Comment EVERY ignore line between those
two markers by prefixing `# ` (keep the marker lines as-is). That block covers
`data/`, `reports/render/`, `*.parquet`, `*.json`, `*.csv`, `*.xls`, `*.xlsx`.
Comment, do not delete, so the original intent stays visible.

Notes worth telling the user:
- This un-ignores `*.json` / `*.csv` / etc. repo-wide, not only under `data/` -
  the intended tradeoff of using these patterns.
- `reports/render/` becomes committable too, but step 4 only LFS-tracks
  `data/**`, so render output would commit as plain git, not LFS.

If an older project lacks the marker lines, comment the equivalent data lines
individually.

## 4. Track data with LFS

- `git lfs track "data/**"` - writes/updates `.gitattributes` with the LFS filter
  for everything under `data/`. Do this BEFORE staging any data: files added
  before they are tracked land in plain git and need `git lfs migrate` to fix.

## 5. Commit the LFS configuration

- `git add .gitattributes .gitignore`
- `git commit -m "Configure Git LFS tracking"`

Commit only the LFS config here. Staging the actual data (`git add data/` then a
commit) is a deliberate follow-up - mention it but let the user decide what data
to commit.

## 6. Report

State what happened: the lfs version, whether `git lfs install` or `git init`
were needed, which `.gitignore` lines were commented, and the tracked pattern.
Remind the user that new files under `data/` now go to LFS, and that committing
existing data is the next step.

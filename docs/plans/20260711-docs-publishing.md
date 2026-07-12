# Plan: changelog conventions, version/compat contract, and library interop
# (for the oryxflow-claude-plugin repo)

> Paste this to the coding agent working in `oryxflow-claude-plugin`. It is self-contained.
> It coordinates with a sibling plan being executed in the **library** repo (`oryxflow`); the
> library-side deliverables this plan depends on are listed under "Cross-repo dependencies".

## Context

The oryxflow docs are "AI-native": every surface has two readers — a human and an AI coding
agent — and the goal is that the *same* artifact serves both. This plugin is the surface that is
**guaranteed to be in the agent's context** (its skill files load when the skill activates); the
library is invisible to the agent until something points at it. That asymmetry drives the whole
plan: **the plugin is where the agent is taught where the library is and when to consult it.**

A consuming-agent review surfaced concrete needs and gaps:

1. **The agent reads changelogs to diagnose regressions**, not to browse. After a library or
   plugin upgrade it wants to: *grep the changelog for the failing symbol, read entries from the
   installed version forward, prioritize breaking ones.* That only works if changelog entries are
   symbol-level, breaking changes are a grep target, and the running version is introspectable.

2. **The pointer must live in the skill.** "The best changelog in the world stays invisible without
   the pointer in the skill." Do **not** inline changelog content into the skill (bloats every
   session for something needed twice a year) — point at it.

3. **Version skew is dangerous.** Plugin is `26.7.3`; library is `26.6.6`. Because the skill
   instructs the agent based on *library behavior*, a mismatch means the agent can't tell a real
   bug from "the skill has run ahead of the library." The plugin must state a **compatibility
   contract** so the agent can detect skew and say so instead of chasing a phantom.

4. **Humans committed to using Claude have no rendered home for best practices / updates.** The
   content already exists and is already human-readable (`skills/oryxflow/conventions.md` is
   written "How We Organize a Project"; `ml-patterns.md`; `docs/CHANGELOG.md` is Keep-a-Changelog),
   but it lives in source folders nobody browses. This is a *surfacing* problem, not an authoring
   one — the fix is links, not new prose, and NOT duplicating it into the library docs (that would
   drift).

### Design decisions (decided across both repos; do not relitigate)

- **One `CHANGELOG.md` per repo, no second machine format.** Structure is the machine-readability.
- **Authority split:** the **library `CHANGELOG.md` is the source of truth for API/behavior**; this
  plugin's changelog covers skill/guidance changes + the compat contract. **When they disagree
  about behavior, the library wins.** State this sentence in the skill so the agent applies it.
- **Three load-bearing changelog tokens, same as the library:** a bullet-leading `BREAKING:`
  token (grep target), a same-bullet `Migration:` old→new clause, and **backticked symbols /
  command names** (`` `/oryxflow:init-project` ``, `` `run.py` ``, a scaffold file path) — never
  prose like "reworked the scaffold".
- **Plugin "breaking" ≠ API breaking.** The plugin has no API; its breaking surface is the
  **scaffold floor, the commands, and the enforced conventions**. A breaking plugin change is one
  that makes an *already-scaffolded* project out of date — so each `BREAKING:` bullet ends with the
  migration action the plugin already ships: run `/oryxflow:update-project` (floor drift) or
  `/oryxflow:check-standards` (convention drift).
- **Cross-repo links use `raw.githubusercontent.com` for the agent, `blob` for humans.** The agent
  must fetch (files are never auto-in-context); the raw URL returns clean markdown, the blob URL
  returns HTML chrome. For the *installed* plugin the agent has the skill on disk (no fetch); the
  fetch that matters is the **library** changelog read from inside a user's project.
- **Keep the skill lean.** The pointer is a few lines; the content stays in the changelogs.

## Implementation

### 1. Add the changelog-consult pointer to the skill

Put this in `skills/oryxflow/reference.md` (the on-demand library reference) and a one-line
trigger to it in `skills/oryxflow/SKILL.md`. Refined from the consuming agent's own wording so the
range is actionable and the failure mode is named:

> **Diagnosing a regression / version bump.** On an unexpected `AttributeError` / `ImportError` /
> `TypeError` from the workflow library, or right after a version bump, *before assuming a code
> bug*: confirm the running library version with `oryxflow.__version__`, then grep the changelog
> for the failing symbol and read entries from the installed version forward, prioritizing
> `BREAKING:` entries.
> - Library (source of truth for API/behavior) — changelog:
>   `https://raw.githubusercontent.com/oryxintel/oryxflow/main/CHANGELOG.md`
>   (rendered: https://oryxflow.readthedocs.io/en/stable/changelog.html). In an editable checkout,
>   `git log --oneline <old>..<new>` in the library repo is the live equivalent.
> - Plugin (skill/guidance + compat contract) — changelog:
>   `https://raw.githubusercontent.com/oryxintel/oryxflow-claude-plugin/main/docs/CHANGELOG.md`.
> - **Authority: when the two disagree about library behavior, the library wins.** If the plugin
>   version and `oryxflow.__version__` violate the compatibility contract below, say so — do not
>   debug a phantom.
> - After any library version change in a project, re-run `python run.py` as a cheap regression
>   smoke test (this scaffold has no version pin and imports oryxflow across several files, so a
>   library switch silently changes behavior).

Keep it to that block — do not paste changelog contents into the skill.

### 2. State the compatibility contract

Decide the supported library floor for the current plugin line and state it in **two** places so
both the human and the agent see it:

- Top of `docs/CHANGELOG.md`, under the title:
  `> Compatibility: plugin 26.7.x targets oryxflow >= <FLOOR>.`  (Fill `<FLOOR>` — note the current
  skew: plugin `26.7.3` vs library `26.6.6`; pick the floor the skill actually assumes, and if it
  assumes library features not yet released, that is itself the thing to flag.)
- A one-line `Compatibility:` note in the `SKILL.md` front-matter body or its header section, so
  the agent has it in context without a fetch.

Going forward, bump/annotate this line whenever the skill starts depending on new library behavior.

### 3. Retrofit the changelog conventions into `docs/CHANGELOG.md`

The file is already Keep-a-Changelog and human-readable. Add the machine-consumability discipline:

- Add a short convention header (mirrors the library's) documenting the `BREAKING:` +
  `Migration:` + backticked-symbol rules, so future entries follow it.
- Sweep existing entries: wherever an entry changed the scaffold floor / a command / an enforced
  convention in a way that affects existing projects, prefix a `BREAKING:` bullet and add a
  `Migration:` clause naming the fix command (`/oryxflow:update-project` or
  `/oryxflow:check-standards`). Most current entries are additive — leave those as-is; do not
  invent breaks.
- Ensure every entry names the concrete symbol/command/file in backticks.

### 4. Surface best practices + "what's new" from the README (human home)

The committed-to-Claude human needs a rendered home for these; the content already exists. Add two
short README sections that link (do not duplicate):

- **Best practices** — link `skills/oryxflow/conventions.md` (house layout / naming / code-org) and
  `skills/oryxflow/ml-patterns.md` (ML task templates). One line each on what they cover. These are
  the *same files the skill loads* — one source, two readers.
- **What's new** — link `docs/CHANGELOG.md`, and state the pull-based update reality: users learn
  there is something new only by running `/plugin marketplace update oryxflow`; the version bump in
  `plugin.json` is the machine signal, the changelog is the human record. Tell users to run update
  periodically.

(If these grow, a tiny MkDocs/RTD site over `skills/*.md` + `docs/CHANGELOG.md` renders the *same*
files — still no duplication. Not needed yet.)

### 5. (Optional) mirror the changelog CI discipline

If the library repo adds a `check_changelog.py` (it is planned to), add the equivalent here so the
`BREAKING:`/`Migration:`/backtick conventions do not rot: assert dated version headings, and that
every `BREAKING:` bullet has a `Migration:` clause. Wire into the existing `.githooks/pre-commit`.

## Cross-repo dependencies (the library plan delivers these)

The pointer in step 1 is inert until the library side ships:

- `oryxflow.__version__` resolves (via `importlib.metadata`) — needed for "confirm the running
  version".
- `CHANGELOG.md` exists at the library repo root with the shared conventions, reachable at
  `raw.githubusercontent.com/oryxintel/oryxflow/main/CHANGELOG.md`.
- The RTD changelog page at `https://oryxflow.readthedocs.io/en/stable/changelog.html`.
- `setup.py` `project_urls` exposing the Changelog URL on PyPI.

If you execute this plugin plan before the library plan lands, the pointer URLs will 404 until the
library changes are pushed — acceptable to write them now (they are the agreed stable paths), but
verify they resolve before cutting a plugin release that advertises them.

## Files modified (plugin repo)

- `skills/oryxflow/reference.md` — add the regression/changelog-consult pointer block (step 1).
- `skills/oryxflow/SKILL.md` — one-line trigger to the pointer + the `Compatibility:` note (steps 1, 2).
- `docs/CHANGELOG.md` — compat contract header + convention header + `BREAKING:`/`Migration:` sweep
  of existing entries (steps 2, 3).
- `README.md` — "Best practices" and "What's new" link sections (step 4).
- `.githooks/pre-commit` (+ a small check script) — optional changelog lint (step 5).

## Verification

- In a project with the plugin active, ask the agent to state the library version — it uses
  `oryxflow.__version__` and reports a real number, not "unknown".
- `grep -n "BREAKING:" docs/CHANGELOG.md` returns entries; each such line also contains
  `Migration:`.
- The `Compatibility:` line appears in both `docs/CHANGELOG.md` and `SKILL.md`.
- Fetching each raw changelog URL in the pointer returns clean markdown (library URL resolves once
  the library plan lands).
- README renders on GitHub with working links to `conventions.md`, `ml-patterns.md`, and
  `docs/CHANGELOG.md`.
- Skill still activates and behaves unchanged (the pointer is reference/guidance, not a new
  behavior); no bloat added to the always-loaded `SKILL.md` beyond the trigger + compat line.

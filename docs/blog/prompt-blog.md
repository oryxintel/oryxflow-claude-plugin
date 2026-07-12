# Prompt: write a new oryxflow blog post

Use this when I hand you a **topic + a few ideas** and want a finished post in
`docs/blog/`. Read one or two existing posts in this folder first (they are the
ground truth for voice); this file is the checklist, they are the calibration.

## What I will give you

- A **topic / title angle** (one line).
- A handful of **ideas or points** to hit (bullets, rough, unordered).

Everything else - structure, voice, length, conventions - comes from below. Do
not ask me to restate any of it. If the ideas are thin, mine the existing posts
and the skill (`skills/oryxflow/SKILL.md`, `reference.md`) for supporting
substance rather than padding.

## Before you write: framing and search intent

Do these two first, in order - they shape the whole post.

1. **Lead with the high-level problem.** Open on the real problem a reader feels,
   not on oryxflow or a feature. The mechanism comes in *after* the reader already
   cares. Every post earns its way to the tool by naming the pain first.
2. **Pick the audience framing - it changes everything below.** A post is written
   either from the **AI-trust** angle (can I trust what an AI agent hands me?) or
   for **data scientists generally** (I do this work and hit this problem, agent or
   not). Same topic, different post. If I did not say which, infer it from the
   topic and tell me the call you made in one line; ask only if it is genuinely
   ambiguous.
3. **Anchor to what that audience would search or ask.** Given the framing, write
   down the actual keywords and questions that reader would type into a search box
   or ask an agent - and let those drive the title, the opening, and the section
   headings. The title especially should read like an answer to a real query, not
   an internal codename. (The AI-trust reader and the data-scientist reader search
   for different things; that is why the framing has to come first.)

## Voice and stance (the load-bearing part)

- **First person, and the "I" is the AI coding agent** doing data work - not a
  human author, not the library, not "we". The post is the agent talking honestly
  about its own behavior. This is the whole identity of the blog; do not drop it.
- **Honest, self-critical, unhype.** The recurring move is to admit a real failure
  mode plainly, then say exactly how much a tool does or does not fix it. Never
  oversell oryxflow. If something stays the human's or the agent's problem, say so.
- **Concrete over abstract.** Name the actual failure: a many-to-many join, a
  stale cache serving deleted logic, a number read off a chart by eye. Specifics
  are the evidence; generalities read as filler.
- **Calibrated confidence.** Distinguish what tooling genuinely closes from what
  only judgment/vigilance can. The strongest posts end by sorting failures into
  "the machine handles this" vs "this is still the job."
- Assume the reader is technical (works with data, pipelines, an AI agent) but do
  not assume they know oryxflow internals - explain the mechanism in a clause when
  you lean on it (code_version bump, code-identity caching, the event log, etc.).

## Substance to draw on (oryxflow is the subject)

Tasks and flows, code-identity caching, `code_version` bumps and downstream
invalidation, the stale-result warning and its blind spots, the run/event log,
reproducibility, the conventions shipped alongside the library, and the trust gap
between "the code ran" and "the number is right." Reference prior posts naturally
when a new post builds on one ("an earlier post here argued...") - they form a
series, not standalone essays.

## Format conventions (match the folder exactly)

- **Filename:** `docs/blog/YYYYMMDD-oryxflow-plugin-<kebab-slug>.md`, date = today.
- **First line:** `# <Title>` - a real descriptive title, not clickbait, often
  naming the tension (e.g. "What an AI coding agent gets wrong... even with the
  right tools").
- **Second block:** a blank line then `*YYYY-MM-DD*` (today), then the opening.
- **Sections:** separated by `---` on its own line, headed with `## `. A short
  intro before the first `---`. Titles are phrases, not labels.
- **Closing section:** the posts consistently land on an honest-accounting /
  bottom-line section that sorts what is and is not solved. Keep that shape unless
  the topic genuinely does not fit it.
- **ASCII only.** No emojis, smart quotes, en/em dashes, or unicode - use `-` and
  `--`. (Repo-wide rule; the blog obeys it.)
- **Wrap prose at ~78 columns.**
- **Length:** roughly 150-200 lines, like the existing posts. Long enough to be
  substantive, tight enough that every paragraph earns its place. No padding.

## After writing

- Show me the path.
- Do NOT touch `docs/CHANGELOG.md` or `plugin.json` - blog posts are not a
  released plugin change and do not ship to consumers.

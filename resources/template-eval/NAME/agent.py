"""The function under test, called the way production calls it.

One rule holds this file together: it IMPORTS the live implementation, it never
carries a copy of it. A second copy of the prompt / instructions inside evals/
drifts from the shipping one the first time either is edited, and an eval scoring
the copy measures nothing. If something has to change to make the entry point
callable from here, change it in production.

Production code is importable because evals/_env.py says how (an installed
package, or a path it adds) - import _env BEFORE production code.
"""
from _env import ROOT  # first: _env makes the production import below resolve

import oryxflow.evals as ev
from pydantic import BaseModel

# PLACEHOLDER SCAFFOLD - import the PRODUCTION entry point here; delete this line when filled.
from myapp.assistant import respond

# The baseline is a git ref - the commit before the change - and the files the arms
# read. PROMPT_GLOBS is what the live arm hashes into its code_version().
# PLACEHOLDER SCAFFOLD - the plan's baseline ref and prompt paths; delete this line when filled.
BASELINE_REF = 'HEAD~1'
PROMPT_PATHS = ['prompts']
PROMPT_GLOBS = ['prompts/*.jinja2']


class Inputs(BaseModel):
    """One case's inputs - one field per non-metadata column in cases.csv.

    load_cases() routes columns by name against this model, so a misspelled column
    lands in metadata and pydantic then raises naming the field it never got. That
    check is what makes keeping cases in a spreadsheet safe.
    """
    # PLACEHOLDER SCAFFOLD - the fields one case supplies; delete this line when filled.
    request: str
    context: str = ''


class Output(BaseModel):
    """What one case produced. Nothing here is capped, trimmed or normalized.

    The metric reads these fields, so a length cap applied here scores the harness's
    own scissors instead of the model - an observed failure, and one that presents
    as a plausible model result. The framework already emits every long field twice:
    `<field>` in full, which is what the metric reads, and `<field>_preview` capped
    for display (TaskEval.preview_chars).

    It is STORED and re-scored later, so carry everything a scorer needs - the tool
    calls made, if one checks them: the run's trace is not stored.
    """
    # PLACEHOLDER SCAFFOLD - the fields the metric and guardrail read; delete this line when filled.
    message: str
    acted: bool


def prompt_root(arm):
    """Where THIS arm reads its prompts from: the working tree, or a git ref.

    A baseline is CHECKED OUT, never rebuilt by string replacement: a replacement
    cannot restore a section the change deleted, cannot put one back where it was,
    and decays silently as the live template moves. Both branches return a directory
    holding the same PROMPT_PATHS layout, so the loader below does not care which
    arm it got. ev.Variant(old, new) is for a PROBE arm - a rewrite that has not
    shipped, so there is no ref - and it raises when its anchor text is gone.
    """
    if arm == 'live':
        return ROOT
    return ev.git_tree(BASELINE_REF, PROMPT_PATHS, repo=ROOT)


async def run_case(inputs, prompt_version='live'):
    """Run ONE case through production and return its Output.

    `async` because `concurrency` is scheduled as coroutines: a plain `def` here
    returns the same numbers but blocks the loop, so the cases run one at a time
    and the concurrency you asked for silently does nothing (8 half-second cases
    at concurrency=8: 1.0s async, 4.9s sync).

    Let exceptions RAISE. Catching one here and returning it in a field makes the
    runner record a SUCCESSFUL case: the failure list comes back empty, the failure
    rate reads zero, the metric scores an error string as if it were an answer, and
    filtering them out becomes a manual job downstream. Raising is what puts the
    case in the failure list, keeps it out of every rate, and lets retry_task work.
    """
    # PLACEHOLDER SCAFFOLD - call the production entry point; delete this line when filled.
    reply = await respond(inputs.request, context=inputs.context,
                          prompt_root=prompt_root(prompt_version))
    return Output(message=reply.message, acted=bool(reply.actions))

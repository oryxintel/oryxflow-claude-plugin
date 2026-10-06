"""The eval: one cached cell per arm, judged on one metric against a guardrail.

README.md (written by /oryxflow:eval-plan) records what this measures and why -
the metric, the guardrail, the baseline, the judgement calls and the known gaps.
Read it before changing anything here.

Run this from its own directory. Paths are relative, so a run from anywhere else
fails immediately on cases.csv rather than quietly building a second cache.

    python run_eval.py --check
    python run_eval.py --prompt-version live --prompt-version baseline --repeats 3
"""
import oryxflow
import oryxflow.evals as ev
from pydantic_evals import Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

import agent

# A `holdout` row is dropped here and counted on CASES.excluded: a case whose text
# is embedded in the prompt is scored against its own answer key, in every arm.
# PLACEHOLDER SCAFFOLD - cases.csv still holds its 3 placeholder rows; delete this line when /oryxflow:eval-cases has replaced them.
CASES = ev.load_cases('cases.csv', inputs=agent.Inputs)


class OutputOk(Evaluator):
    """Score ONE case. The class name is the column the metric reads.

    Deterministic wherever it can be: when the output is one of a fixed set of
    labels, scoring it is a comparison, not a judging job. Reach for an LLM judge
    only for genuinely fuzzy quality - and then from a DIFFERENT model family than
    the one under test (self-preference is real and avoiding it is free), on the
    RAW output rather than anything a sanitizer touched, and with no optional
    fields (a flag the model can decline to fill reads downstream as a pass).

    For ONE yes/no question, do not write this class at all - pydantic-evals
    ships the judge: `LLMJudge(rubric='...', model=<a different family>,
    include_input=True)` in the dataset's evaluators, and `ev.Metric(label,
    'LLMJudge')` reads it. Keep a custom Evaluator for several fields per case or
    a verdict per item inside the output.

    An LLM judge belongs HERE, not inside agent.run_case(): scoring is the
    evaluator's job, a judge failure is then a scoring failure rather than a lost
    case, and returning a dict gives each verdict field its own frame column
    instead of flattening them into Output by hand. Judge asynchronously - the
    method is still named `evaluate`, just `async def` - or the judge call blocks
    the loop and the cases stop running concurrently. Return `{}` for a case there
    is nothing to judge; those rows read as NOT MEASURED, which is not a failure.
    """

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        # PLACEHOLDER SCAFFOLD - the plan's scoring rule; delete this line when filled.
        return bool(ctx.output.message.strip())


class PromptEval(ev.TaskEval):
    """PLACEHOLDER SCAFFOLD - one line: the question this eval answers; delete this line when filled."""

    # One Parameter per arm axis. Each becomes a repeatable CLI flag
    # (--prompt-version) and each value is one cached cell.
    # PLACEHOLDER SCAFFOLD - the axis the plan compares; delete this line when filled.
    prompt_version = oryxflow.ChoiceParameter(default='live', choices=['live', 'baseline'])

    dataset = Dataset(name='cases', cases=CASES, evaluators=[OutputOk()])

    # Coverage is read FIRST and the quality rate second, never alone: a rate over a
    # filtered subset improves as the subset shrinks, so a prompt can score well on
    # quality by staying silent on a third of the cases. `where` is that filter and
    # `coverage=` is the companion that keeps the number honest.
    # PLACEHOLDER SCAFFOLD - the plan's metric and its coverage metric; delete this line when filled.
    metric = ev.Metric('quality', 'OutputOk', where='acted',
                       coverage=ev.Metric('action rate', 'acted', where='~control'))

    # Mandatory, never optional: without it a prompt that acts on EVERYTHING scores
    # 100% on "did it act" and ships a regression. The controls are the cases where
    # doing nothing is correct, so acting on one is a false positive.
    # PLACEHOLDER SCAFFOLD - the plan's guardrail; delete this line when filled.
    guardrail = ev.Metric('false action rate', 'acted', where='control',
                          higher_is_better=False, budget=0.05)

    # metadata columns worth breaking the metric down by. Keep `synthetic`: the
    # headline is real cases only, with the invented ones reported beside it.
    slices = ('kind', 'synthetic')

    # Conscious knobs, uncomment to change:
    # preview_chars = 200    # display cap for `<field>_preview`; `<field>` is never cut
    # max_failure_rate = 0.2 # above this the run saves NOTHING - a parquet of
    #                        # exceptions is indistinguishable from a measurement
    # preflight = None       # default runs case() once (what `--check` costs)

    async def case(self, inputs):
        return await agent.run_case(inputs, prompt_version=self.prompt_version)

    def code_version(self):
        """The bytes that actually decide this arm's result.

        Edit a prompt and re-run: the arms that read it recompute, the others are
        served from cache. That is the whole trick - no --reset to remember, and no
        stale cell reported as a fresh number. A baseline arm returns the RESOLVED
        sha, never the ref string: 'HEAD~1' names different content after every
        commit, and a cache key that moves under a stable-looking name is exactly
        the failure this guards against.
        """
        if self.prompt_version == 'baseline':
            return ev.git_sha(agent.BASELINE_REF, repo=agent.ROOT)
        # PLACEHOLDER SCAFFOLD - the prompt/template files the live arm reads; delete this line when filled.
        return oryxflow.hash_files(*agent.PROMPT_GLOBS, root=agent.ROOT)

"""Run this eval. The flags are DERIVED from the task's Parameters, so adding a
Parameter adds its flag and there is no second place to keep in sync.

    python run_eval.py --check                     # preflight only: one call
    python run_eval.py --prompt-version live --prompt-version baseline --repeats 3

Built-ins on top of the derived flags: --repeats --concurrency --reset --check
--csv --yes. The projected calls, the cached/new split and the cost estimate are
printed before anything is billed; --yes answers that confirmation in advance.
"""
import oryxflow.evals as ev

from eval import PromptEval

if __name__ == '__main__':
    ev.cli(PromptEval)

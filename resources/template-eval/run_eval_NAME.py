"""Run the NAME eval. The flags are DERIVED from the eval's Parameters, so adding
a Parameter adds its flag and there is no second place to keep in sync.

Launch from evals/ - the shared cache (data/) and _env.py live there:

    cd evals
    python run_eval_NAME.py --check                  # preflight only: one call
    python run_eval_NAME.py --prompt-version live --prompt-version baseline --repeats 3

Built-ins on top of the derived flags: --repeats --concurrency --reset --rescore
--check --csv --yes. The projected calls, the cached/new split and the cost
estimate are printed before anything is billed; --yes answers that confirmation
in advance. --rescore re-runs only the scorers over the stored outputs.
"""
import oryxflow.evals as ev

from NAME.eval import PromptEval

if __name__ == '__main__':
    ev.cli(PromptEval)

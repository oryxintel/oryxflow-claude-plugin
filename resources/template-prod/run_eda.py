# run_eda.py <topic> - COMPARISON tier: run many variants side by side (heavy
# experiments / A-B). run.py is the fast inner loop on ONE active param set;
# reach here only to COMPARE a named set at once. A graduated add-on: copied
# from the plugin's resources/template-prod/. See the plugin's conventions.md
# "Run tiers by lifecycle".
#
# Add a topic as a registry ENTRY below (data) - never add another run_*.py
# (code). That is what keeps this to ~3 run files instead of 20.
import sys

import oryxflow

import cfg, tasks
from flow_params import params

# topic -> (terminal task, variants keyed by flow name). Each variant is the
# base `params` plus the one axis you are sweeping.
TOPICS = {
    'models': (tasks.FinalTask, {                        # PLACEHOLDER SCAFFOLD - real topics
        'lgbm': {**params, 'model': 'lgbm'},
        'xgb':  {**params, 'model': 'xgboost'},
    }),
}

topic = sys.argv[1] if len(sys.argv) > 1 else None
if topic not in TOPICS:
    sys.exit(f"usage: python run_eda.py <{'|'.join(TOPICS)}>")

oryxflow.enable_logging()
task, variants = TOPICS[topic]
wf = oryxflow.WorkflowMulti(task, variants, env=cfg.env)  # experiment env, NOT prod
res = wf.run()
print(res.summary())                                     # res['lgbm'] -> one flow's RunResult

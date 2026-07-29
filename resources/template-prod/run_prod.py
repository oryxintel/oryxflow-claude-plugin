# run_prod.py - PROD tier: frozen settings, KEPT outputs. This is NOT the
# experiment path (that stays run.py). A graduated add-on: copied from the
# plugin's resources/template-prod/ when a project first goes to prod. See the
# plugin's conventions.md "Run tiers by lifecycle" for the full rationale.
import oryxflow

import cfg, tasks
from flow_params import params_prod

oryxflow.enable_logging()

# Build the prod workflow INLINE - do NOT import flow.py's `flow`. That singleton
# is bound at import time to the EXPERIMENT tier (cfg.env, params); prod needs
# its own (params_prod, env='prod') object so the two tiers never share identity
# or clobber each other's cache/state.
#
# Prod usually runs several frozen variants (one per segment/period). Build them
# from params_prod + the prod axis, keyed by name so results are labelled. Use
# this when the variants are SEPARATELY managed (own summary, own reset scope);
# when they belong in ONE cached deliverable, fan out instead with a RunAll...Prod
# task (@oryxflow.requires_each). For a SINGLE frozen run, drop the dict:
#   wf = oryxflow.Workflow(tasks.FinalTask, params_prod, env='prod')
variants = {seg: {**params_prod, 'segment': seg}         # PLACEHOLDER SCAFFOLD - the prod axis
            for seg in cfg.segments}
wf = oryxflow.WorkflowMulti(tasks.FinalTask, variants, env='prod')  # PLACEHOLDER SCAFFOLD - terminal task

# Selective reset by COST + AUTHORITY: refresh ONLY the cheap, fast-moving LOCAL
# source so a new period picks up fresh inputs; NEVER reset the expensive /
# external pulls - those are the frozen "trusted" baseline that must persist
# unchanged across prod runs (resetting them would recompute the numbers prod
# exists to hold steady).
wf.reset(tasks.DataLocalReload)        # PLACEHOLDER SCAFFOLD - cheap reload: REFRESH
# do NOT reset tasks.DataExternalPull  # slow/external pull: FROZEN baseline

result = wf.run()
print(result.summary())                # per-variant blocks; result['<seg>'] to drill in

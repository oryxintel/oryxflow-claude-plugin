import d6tflow

import cfg
import tasks
from flow_params import params

# task=tasks.GetData
task=tasks.Process

flow = d6tflow.Workflow(task=task, params=params, env=cfg.env)

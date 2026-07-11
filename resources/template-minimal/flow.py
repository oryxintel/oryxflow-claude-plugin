import oryxflow

import cfg
import tasks
from flow_params import params

# task=tasks.GetData
task=tasks.Process

flow = oryxflow.Workflow(task=task, params=params, env=cfg.env)

import d6tflow
from loguru import logger

import cfg, tasks


from flow import flow, task

# flow.reset(tasks.GetData)   # after editing a task's CODE, reset it (cascades downstream)
d6tflow.enable_logging()      # d6tflow logs the task lifecycle (scheduling/completion/timing)
flow.preview()
logger.info("running {} env={}", task.__name__, cfg.env)  # loguru = DOMAIN signal; log shapes/metrics in run()
flow.run()


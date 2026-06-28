import d6tflow

import cfg, tasks


from flow import flow, task

# flow.reset(tasks.GetData)   # after editing a task's CODE, reset it (cascades downstream)
d6tflow.enable_logging()      # one d6tflow stream: task lifecycle + self.logger domain logs
# enable_logging(colorize=False) to force plain (grep-friendly) output; default
# auto-detects (colored on a terminal, plain when redirected to a file / pipe).
print(f"running {task.__name__} env={cfg.env}")  # orchestration banner (not a task -> no self.logger)
flow.preview()
flow.run()


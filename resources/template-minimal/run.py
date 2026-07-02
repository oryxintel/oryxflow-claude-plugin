import d6tflow

import cfg, tasks


from flow import flow, task

# flow.reset(tasks.GetData)   # after editing a task's CODE, reset it (cascades downstream)
d6tflow.enable_logging()      # one d6tflow stream: task lifecycle + self.logger domain logs
# enable_logging(colorize=False) to force plain (grep-friendly) output; default
# auto-detects (colored on a terminal, plain when redirected to a file / pipe).
print(f"running {task.__name__} env={cfg.env}")  # orchestration banner (not a task -> no self.logger)
flow.preview()
result = flow.run()           # RunResult; abort=True (default) RAISES on failure -> native traceback
print(result.summary())       # ran / cache-hit / failed at a glance  (result.success = one-line verdict)
# Inspect result, do not grep the log: result.ran / result.complete (recomputed vs cached),
# result.did_run(tasks.X); to examine a FAILURE structurally without re-running,
# flow.run(abort=False) then result.failed / result.failure_of(tasks.X).


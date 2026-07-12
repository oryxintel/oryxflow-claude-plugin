"""PLACEHOLDER SCAFFOLD - replace with this workflow's goal / overview.

What does this pipeline produce, and why? A few lines here are the project's
top-level documentation - read on every session in place of a separate doc.
"""
import oryxflow
import pandas as pd

import cfg

# PLACEHOLDER SCAFFOLD - replace the tasks below with the real pipeline.
class GetData(oryxflow.tasks.TaskPqPandas):
    """PLACEHOLDER - load this project's raw data and save it for downstream tasks."""
    code_version = 1  # BUMP when you change this task's logic -> it + downstream rerun

    def run(self):
        df = pd.DataFrame({'a':range(10)})
        self.save(df)

@oryxflow.requires(GetData)
class Process(oryxflow.tasks.TaskPqPandas):
    """PLACEHOLDER - transform GetData's output into the pipeline's result."""
    code_version = 1  # BUMP when you change this task's logic -> it + downstream rerun
    optional = oryxflow.BoolParameter(default=False)

    def run(self):
        df = self.input().load()
        if self.optional:
            df = df*2
        self.logger.info("rows={}", len(df))  # in-task domain log; scalars only, save the frame don't log it
        self.save(df)

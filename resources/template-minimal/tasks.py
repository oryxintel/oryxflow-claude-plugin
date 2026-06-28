"""PLACEHOLDER SCAFFOLD - replace with this workflow's goal / overview.

What does this pipeline produce, and why? A few lines here are the project's
top-level documentation - read on every session in place of a separate doc.
"""
import d6tflow
import pandas as pd
from loguru import logger

import cfg

# PLACEHOLDER SCAFFOLD - replace the tasks below with the real pipeline.
class GetData(d6tflow.tasks.TaskPqPandas):
    """PLACEHOLDER - load this project's raw data and save it for downstream tasks."""

    def run(self):
        df = pd.DataFrame({'a':range(10)})
        self.save(df)

@d6tflow.requires(GetData)
class Process(d6tflow.tasks.TaskPqPandas):
    """PLACEHOLDER - transform GetData's output into the pipeline's result."""
    optional = d6tflow.BoolParameter(default=False)

    def run(self):
        df = self.input().load()
        if self.optional:
            df = df*2
        logger.info("rows={}", len(df))  # log the result's shape/metrics (scalars); save the frame, don't log it
        self.save(df)

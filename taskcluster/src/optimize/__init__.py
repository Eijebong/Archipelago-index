import logging
from datetime import datetime

from taskcluster.exceptions import TaskclusterRestFailure
from taskgraph.optimize.base import Any, OptimizationStrategy, register_strategy
from taskgraph.optimize.strategies import SkipUnlessChanged, IndexSearch
from taskgraph.util.taskcluster import find_task_id, status_task

from . import schema

logger = logging.getLogger("optimization")


class IndexSearchIncludeFailed(OptimizationStrategy):
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ"

    def should_replace_task(self, task, params, deadline, index_paths):
        for index_path in index_paths:
            try:
                task_id = find_task_id(index_path)
                status = status_task(task_id)

                if deadline and status and datetime.strptime(
                    status["expires"],
                    self.fmt,
                ) < datetime.strptime(deadline, self.fmt):
                    logger.debug(
                        f"not replacing {task.label} with {task_id} because it expires before {deadline}"
                    )
                    continue

                return task_id
            except (KeyError, TaskclusterRestFailure):
                pass

        return False


def split_args(*args, **kwargs):
    return [args[0]['index-path'], args[0]['skip-unless-changed']]


@register_strategy("skip-unless-changed-or-cached", ())
class SkipOrCache(Any):
    def __init__(self, **kwargs):
        super().__init__(IndexSearch(), SkipUnlessChanged(), split_args=split_args, **kwargs)

    description = "Skip unless changed or use cached PR task if possible"


@register_strategy("skip-unless-changed-or-attempted", ())
class SkipOrAttempted(Any):
    def __init__(self, **kwargs):
        super().__init__(IndexSearchIncludeFailed(), SkipUnlessChanged(), split_args=split_args, **kwargs)

    description = "Skip unless changed or use attempted (including failed) PR task if possible"


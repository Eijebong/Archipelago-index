import copy
import json
import os

from taskgraph.transforms.base import TransformSequence
from taskgraph.util.taskcluster import find_task_id, list_artifacts, get_artifact

transforms = TransformSequence()

@transforms.add
def generate_tasks(config, tasks):
    comment = os.environ.get("TASKCLUSTER_COMMENT")
    if comment != "r+":
        print("Not generating merge tasks as it didn't come from a valid comment:", comment)
        return

    pr_number = os.environ.get("ARCHIPELAGO_INDEX_PULL_REQUEST_NUMBER")
    if pr_number is None:
        print("Not a PR, ignoring transform merge, graph will be incomplete. Set `ARCHIPELAGO_INDEX_PULL_REQUEST_NUMBER` to a valid PR number")
        return

    for task in tasks:
        new_task = copy.deepcopy(task)
        deps = new_task.setdefault("dependencies", {})
        for dep in config.kind_dependencies_tasks:
            deps[dep] = dep
        yield new_task

def create_task_for_apworld(original_task, apworld, version):
    task = copy.deepcopy(original_task)
    env = task["worker"].setdefault("env", {})
    env["TEST_APWORLD_NAME"] = apworld
    env["TEST_APWORLD_VERSION"] = version
    task["label"] = f"test-{apworld}-{version}"

    return task



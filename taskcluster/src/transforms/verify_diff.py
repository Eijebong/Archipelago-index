import copy
import json
import os
import toml
from pathlib import Path

from taskgraph.transforms.base import TransformSequence
from taskgraph.util.taskcluster import find_task_id, list_artifacts, get_artifact

transforms = TransformSequence()
DIFF_INDEX_PATH = "ap.archipelago-index.index.pr"

@transforms.add
def generate_tasks(config, tasks):
    pr_number = os.environ.get("ARCHIPELAGO_INDEX_PULL_REQUEST_NUMBER")
    if pr_number is None:
        print("Not a PR, ignoring transform verify_diff, graph will be incomplete. Set `ARCHIPELAGO_INDEX_PULL_REQUEST_NUMBER` to a valid PR number")
        return

    try:
        diff_task = find_task_id(f"{DIFF_INDEX_PATH}.{pr_number}.latest")
    except KeyError:
        print(f"No diff yet for PR {pr_number}, not generating verify tasks")
        return

    tasks = list(tasks)
    for artifact in list_artifacts(diff_task):
        if not artifact['name'].startswith('public/diffs/'):
            continue

        diff_name = artifact['name'].removeprefix('public/diffs/')
        diff_response = get_artifact(diff_task, artifact['name'])
        if diff_response.status != 200:
            raise Exception("Failed to fetch artifact {}".format(artifact["name"]))
        diff = json.loads(diff_response.read())

        for task in tasks:
            env = task["worker"].setdefault("env", {})
            env["TEST_ALL"] = "0"
            yield from create_check_tasks_from_diff(task, diff)


def create_check_tasks_from_diff(task, diff):
    world_name = diff["world_name"]
    apworld_name = diff["apworld_name"]
    for version_range, diff_status in diff["diffs"].items():
        if "VersionAdded" not in diff_status:
            continue
        _, new_version = version_range.split('...', 1)
        yield create_task_for_apworld(task, world_name, apworld_name, new_version, {"diff": "diff-index"})


def create_task_for_apworld(original_task, world_name, apworld_name, version, dependencies=None):
    task = copy.deepcopy(original_task)
    env = task["worker"].setdefault("env", {})
    env["TEST_WORLD_NAME"] = world_name
    env["TEST_APWORLD_NAME"] = apworld_name
    env["TEST_APWORLD_VERSION"] = version
    task["label"] = f"{original_task['name']}-{apworld_name}-{version}"

    if dependencies is not None:
        task["dependencies"] = dependencies
    if original_task['name'] == "ap-test":
        task["dependencies"]["check"] = f"check-{apworld_name}-{version}"

    return task


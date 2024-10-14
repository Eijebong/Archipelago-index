import copy
import json
import os
import toml
from pathlib import Path

from taskgraph.transforms.base import TransformSequence
from taskgraph.util.taskcluster import find_task_id, list_artifacts, get_artifact

transforms = TransformSequence()

@transforms.add
def generate_tasks(config, tasks):
    comment = os.environ.get("TASKCLUSTER_COMMENT")
    if comment not in ["test", "r+", "test-all"]:
        print("Not generating verify tasks as it didn't come from a valid comment:", comment)
        return

    for task in tasks:
        pr_number = os.environ.get("ARCHIPELAGO_INDEX_PULL_REQUEST_NUMBER")
        if pr_number is None:
            print("Not a PR, ignoring transform verify_diff, graph will be incomplete. Set `ARCHIPELAGO_INDEX_PULL_REQUEST_NUMBER` to a valid PR number")
            return

        diff_index_path = task.pop('diff-index-path')
        if comment in ["test", "r+"]:
            yield from create_check_tasks_from_diff(task, diff_index_path, pr_number)
        if comment in ["test-all"]:
            yield from create_check_tasks_for_all(task, pr_number)


def create_check_tasks_from_diff(task, diff_index_path, pr_number):
    diff_task = find_task_id(f"{diff_index_path}.{pr_number}.latest")
    if diff_task is None:
        raise Exception("Couldn't find diff task for current PR")

    for artifact in list_artifacts(diff_task):
        if not artifact['name'].startswith('public/diffs/'):
            continue

        diff_name = artifact['name'].removeprefix('public/diffs/')
        diff_response = get_artifact(diff_task, artifact['name'])
        if diff_response.status != 200:
            raise Exception("Failed to fetch artifact {}".format(artifact["name"]))

        diff = json.loads(diff_response.read())
        world_name = diff["world_name"]
        for version_range, diff_status in diff["diffs"].items():
            if "VersionAdded" not in diff_status:
                continue
            _, new_version = version_range.split('...', 1)
            yield create_task_for_apworld(task, world_name, new_version, {"diff": "diff-index"})



def create_check_tasks_for_all(task, pr_number):
    index = toml.load("index.toml")
    for world_path in os.listdir("index/"):
        world = toml.load(os.path.join("index", world_path))
        if world.get("disabled"):
            continue

        apworld_name = Path(world_path).stem
        versions = list(world.get("versions", {}).keys())
        if world.get("supported", False):
            versions.append(index["archipelago_version"])


        for version in versions:
            yield create_task_for_apworld(task, apworld_name, version)


def create_task_for_apworld(original_task, apworld, version, dependencies=None):
    task = copy.deepcopy(original_task)
    env = task["worker"].setdefault("env", {})
    env["TEST_APWORLD_NAME"] = apworld
    env["TEST_APWORLD_VERSION"] = version
    task["label"] = f"test-{apworld}-{version}"

    if dependencies is not None:
        task["dependencies"] = dependencies

    return task


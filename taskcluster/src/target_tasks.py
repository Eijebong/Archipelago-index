from taskgraph.target_tasks import register_target_task
from taskgraph.util.taskcluster import find_task_id, list_artifacts, get_artifact
import taskgraph

from collections import defaultdict
import json
import os
import shlex

DIFF_INDEX_PATH = "ap.archipelago-index.index.pr"


def _filter_for_pr(tasks, force=[]):
    pr_number = os.environ.get("ARCHIPELAGO_INDEX_PULL_REQUEST_NUMBER")
    if pr_number is None:
        print("ARCHIPELAGO_INDEX_PULL_REQUEST_NUMBER missing, returning empty task set")
        return []

    try:
        diff_task = find_task_id(f"{DIFF_INDEX_PATH}.{pr_number}.latest")
    except KeyError:
        print(f"No diff yet for PR {pr_number}, returning empty task set")
        return []

    filtered_tasks = [label for label, task in tasks if task.kind in force]


    for artifact in list_artifacts(diff_task):
        if not artifact['name'].startswith('public/diffs/'):
            continue

        diff_name = artifact['name'].removeprefix('public/diffs/')
        diff_response = get_artifact(diff_task, artifact['name'])
        if diff_response.status != 200:
            raise Exception("Failed to fetch artifact {}".format(artifact["name"]))
        diff = json.loads(diff_response.read())

        for version_range, diff_status in diff["diffs"].items():
            apworld_name = diff["apworld_name"]
            if "VersionAdded" not in diff_status:
                continue
            _, new_version = version_range.split('...', 1)

            suffix = f"-{apworld_name}-{new_version}"

            for label, task in tasks:
                if label.endswith(suffix):
                    filtered_tasks.append(label)

    return filtered_tasks


@register_target_task("diff")
def diff_target_task(full_task_graph, parameters, graph_config):
    return _filter_for_pr([(label, task) for label, task in full_task_graph.tasks.items() if task.kind == "diff-from-lobby"])


@register_target_task("test")
def merge_target_task(full_task_graph, parameters, graph_config):
    return _filter_for_pr([(label, task) for label, task in full_task_graph.tasks.items() if task.kind in {"check", "ap-test"}])


@register_target_task("r+")
def rplus_target_task(full_task_graph, parameters, graph_config):
    return _filter_for_pr([(label, task) for label, task in full_task_graph.tasks.items() if task.kind in {"check", "ap-test", "publish"}], force=["publish"])


@register_target_task("merge")
def merge_target_task(full_task_graph, parameters, graph_config):
    return [label for label, task in full_task_graph.tasks.items() if task.kind == "publish"]


@register_target_task("default")
def default_target_task(full_task_graph, parameters, graph_config):
    if "TRY_CONFIG" in os.environ:
        return try_target_tasks(full_task_graph, os.environ["TRY_CONFIG"])
    return taskgraph.target_tasks.target_tasks_default(full_task_graph, parameters, graph_config)


def try_target_tasks(full_task_graph, try_config):
    targets = parse_try_config(try_config)
    try_tasks = [(label, task) for label, task in full_task_graph.tasks.items() if task.kind in {"ap-test", "check"}]
    filtered_tasks = []

    for (kind, target) in targets.items():
        if target is None:
            filtered_tasks.extend(label for label, task in try_tasks if task.kind == kind)
        else:
            for apworld in target:
                filtered_tasks.extend(label for label, task in try_tasks if task.kind == kind and apworld in label)


    return filtered_tasks


def parse_try_config(try_config):
    if not try_config.startswith("try: "):
        raise RuntimeError("Invalid try config, it should start with `try: `")

    targets = defaultdict(lambda: [])
    try_config = try_config[len("try: "):].strip()
    for config in shlex.split(try_config):
        if ':' in config:
            kind, target = config.split(":", 1)
        else:
            kind = config
            target = None


        # Treat None as a special "everything" in targets, no need to try and schedule specific tasks if that's the case
        # Something like `try: foo foo:bar` would schedule all targets for the `foo` kind, including `bar`

        if target is None:
            targets[kind] = None

        if targets[kind] is None:
            continue

        targets[kind].append(target)

    return targets


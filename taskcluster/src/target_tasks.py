from taskgraph.target_tasks import register_target_task
from taskgraph.util.taskcluster import find_task_id, list_artifacts, get_artifact
import taskcluster.exceptions
import taskgraph

from collections import defaultdict
import os
import shlex

from src.transforms.fuzz_params import extract_raw_fuzz_params


def _is_specific_fuzz(parameters):
    return extract_raw_fuzz_params(parameters) is not None


def _filter_for_pr(tasks, parameters, force=[]):
    pr_number = parameters.get("pull_request_number")
    if pr_number is None:
        print("pull_request_number param missing, returning empty task set")
        return []

    project = parameters.get('project', 'unknown').lower()
    try:
        diff_task = find_task_id(f"ap.{project}.index.pr.{pr_number}.latest")
    except (KeyError, taskcluster.exceptions.TaskclusterRestFailure):
        print(f"No diff yet for PR {pr_number}, returning only forced tasks")
        return [label for label, task in tasks if task.kind in force]

    filtered_tasks = [label for label, task in tasks if task.kind in force]


    for artifact in list_artifacts(diff_task):
        if not artifact['name'].startswith('public/diffs/') or not artifact['name'].endswith('.apdiff'):
            continue

        try:
            diff = get_artifact(diff_task, artifact['name'])
        except Exception as exc:
            raise Exception("Failed to fetch artifact {}".format(artifact["name"])) from exc

        for version_range, diff_status in diff["diffs"].items():
            apworld_name = diff["apworld_name"]

            new_version = None
            if "VersionAdded" in diff_status:
                _, new_version = version_range.split('...', 1)
            full_suffix = f"-{apworld_name}-{new_version}"

            if new_version is None:
                continue

            for label, task in tasks:
                # If we're scheduling update-expectations, schedule them all
                if label.startswith(f"update-expectations-{apworld_name}"):
                    filtered_tasks.append(label)

                if label.endswith(full_suffix):
                    filtered_tasks.append(label)

    return filtered_tasks


@register_target_task("diff")
def diff_target_task(full_task_graph, parameters, graph_config):
    return [label for label, task in full_task_graph.tasks.items() if task.kind in ("diff-from-lobby", "comment")]


@register_target_task("test")
def test_target_task(full_task_graph, parameters, graph_config):
    return _filter_for_pr([(label, task) for label, task in full_task_graph.tasks.items() if task.kind in {"check", "ap-test", "test-report"}], parameters)


@register_target_task("test-fuzz")
def test_fuzz_target_task(full_task_graph, parameters, graph_config):
    return _filter_for_pr([(label, task) for label, task in full_task_graph.tasks.items() if task.kind in {"check", "ap-test", "test-report", "fuzz", "upload-fuzz-results", "fuzz-report"}], parameters)


@register_target_task("r+")
def rplus_target_task(full_task_graph, parameters, graph_config):
    return _filter_for_pr([(label, task) for label, task in full_task_graph.tasks.items() if task.kind in {"check", "ap-test", "test-report", "publish", "upload-fuzz-results"}], parameters, force=["publish"])

@register_target_task("r++")
def rplus_plus_target_task(full_task_graph, parameters, graph_config):
    return _filter_for_pr([(label, task) for label, task in full_task_graph.tasks.items() if task.kind in {"check", "update-expectations", "make-expectations-patch", "ap-test", "test-report", "publish", "upload-fuzz-results"}], parameters, force=["publish", "make-expectations-patch"])

@register_target_task("fuzz")
def fuzz_target_task(full_task_graph, parameters, graph_config):
    specific = _is_specific_fuzz(parameters)
    tasks = [
        (label, task) for label, task in full_task_graph.tasks.items()
        if task.kind in {"fuzz", "fuzz-report"}
        and not (specific and task.attributes.get("fuzz-variant"))
    ]
    return _filter_for_pr(tasks, parameters)

@register_target_task("merge")
def merge_target_task(full_task_graph, parameters, graph_config):
    return [label for label, task in full_task_graph.tasks.items() if task.kind == "publish"]

@register_target_task("default")
def default_target_task(full_task_graph, parameters, graph_config):
    if parameters.get('try_config'):
        return try_target_tasks(full_task_graph, parameters)
    return taskgraph.target_tasks.target_tasks_default(full_task_graph, parameters, graph_config)

@register_target_task("rebuild-ap-worker")
def rebuild_ap_worker_target_task(full_task_graph, parameters, graph_config):
    return [label for label, task in full_task_graph.tasks.items() if task.label == "docker-image-ap-checker"]

@register_target_task("verify-index")
def verify_index_target_task(full_task_graph, parameters, graph_config):
    return [label for label, task in full_task_graph.tasks.items() if task.label == "verify-index"]


def try_target_tasks(full_task_graph, parameters):
    try_config = parameters['try_config'].split('\n')[0]
    targets = parse_try_config(try_config)
    specific = _is_specific_fuzz(parameters)
    try_tasks = [(label, task) for label, task in full_task_graph.tasks.items() if task.kind in {"ap-test", "check", "fuzz", "update-expectations", "make-expectations-patch", "verify-index"}]
    filtered_tasks = []

    for (kind, target) in targets.items():
        if target is None:
            if kind == "fuzz":
                filtered_tasks.extend(
                    label for label, task in _only_latest(try_tasks)
                    if task.kind == kind and not (specific and task.attributes.get("fuzz-variant"))
                )
            else:
                filtered_tasks.extend(label for label, task in try_tasks if task.kind == kind)
        else:
            for apworld in target:
                if kind == "fuzz":
                    filtered_tasks.extend(
                        label for label, task in _only_latest(try_tasks)
                        if task.kind == kind and apworld in label and not (specific and task.attributes.get("fuzz-variant"))
                    )
                else:
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

def _only_latest(tasks):
    return [(label, task) for label, task in tasks if task.attributes.get("latest", False)]

from . import optimize, target_tasks
from eije_taskgraph import register as eije_taskgraph_register
from taskgraph.morph import register_morph
from taskgraph.parameters import extend_parameters_schema
from voluptuous import Optional
import json
import os

def _get_defaults(repo_root=None):
    from taskgraph.parameters import _get_defaults as _upstream_defaults
    defaults = _upstream_defaults(repo_root)
    if "project" in defaults:
        defaults["project"] = defaults["project"].lower()
    return defaults

extend_parameters_schema({
    Optional("pull_request_number"): int,
    Optional("taskcluster_comment"): str,
    Optional("try_config"): str,
}, defaults_fn=_get_defaults)

@register_morph
def handle_soft_fetches(taskgraph, label_to_taskid, parameters, graph_config):
    for task in taskgraph:
        soft_fetches = task.attributes.get("soft-fetches")
        if soft_fetches is None:
            continue

        del task.attributes["soft-fetches"]

        moz_fetches = json.loads(task.task['payload']['env'].get("MOZ_FETCHES", "[]"))
        moz_fetches.extend((
            {
                "artifact": dep["artifact"],
                "dest": dep["dest"],
                "extract": False,
                "task": label_to_taskid[dep_id]
            } for dep_id, dep in soft_fetches.items() if dep_id in label_to_taskid
        ))

        task.task['payload']['env']["MOZ_FETCHES"] = json.dumps(moz_fetches)
        task.task['payload']['env'].setdefault("MOZ_FETCHES_DIR", "fetches")

    return taskgraph, label_to_taskid

@register_morph
def restore_soft_docker_image_dependency(taskgraph, label_to_taskid, parameters, graph_config):
    """Re-add the docker-image soft dependency as a hard dependency.

    The `soft_docker_image` transform demotes the docker-image dep to a soft
    dep so that it doesn't pull cached consumers back into the graph during
    optimization. Once optimization is done, we still want the runtime edge
    so the task actually waits for a freshly built image to land.
    """
    for task in taskgraph.tasks.values():
        if not task.attributes.get("soft-docker-image"):
            continue

        for soft_dep_label in task.soft_dependencies:
            if not soft_dep_label.startswith("docker-image-"):
                continue
            task_id = label_to_taskid.get(soft_dep_label)
            if task_id is None:
                continue
            deps = task.task.setdefault("dependencies", [])
            if task_id not in deps:
                deps.append(task_id)

    return taskgraph, label_to_taskid

@register_morph
def resolve_soft_payload(taskgraph, label_to_taskid, parameters, graph_config):
    """Resolve soft dependencies into payload fields.

    Tasks with a `soft-payload` attribute mapping {dep_label: payload_key} will
    have the payload key set to the dep's task ID if the dep is in the graph,
    or null otherwise.
    """
    for task in taskgraph:
        soft_payload = task.attributes.get("soft-payload")
        if soft_payload is None:
            continue

        del task.attributes["soft-payload"]

        for dep_label, payload_key in soft_payload.items():
            if dep_label in label_to_taskid:
                task_id = label_to_taskid[dep_label]
                task.task["payload"][payload_key] = task_id
                deps = task.task.setdefault("dependencies", [])
                if task_id not in deps:
                    deps.append(task_id)

    return taskgraph, label_to_taskid

STAGING_WORKER_OVERRIDES = {
    "publishscript-3": "publishscript-dev-1",
    "githubscript-1": "githubscript-dev-1",
    "githubscript-3": "githubscript-dev-1",
}

def register(graph_config):
    eije_taskgraph_register(graph_config)

def get_decision_parameters(graph_config, parameters):
    pr_number = os.environ.get('GITHUB_PULL_REQUEST_NUMBER')
    if pr_number is not None:
        parameters['pull_request_number'] = int(pr_number)

    tc_comment = os.environ.get("TASKCLUSTER_COMMENT")
    if tc_comment is not None:
        parameters['taskcluster_comment'] = tc_comment

    try_config = os.environ.get("TRY_CONFIG")
    if try_config is not None:
        parameters['try_config'] = try_config

    project = parameters.get("project", "")
    if project.startswith("staging-"):
        aliases = graph_config['workers']['aliases']
        for alias, override in STAGING_WORKER_OVERRIDES.items():
            if alias in aliases:
                aliases[alias]["worker-type"] = override

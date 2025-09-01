from . import optimize, target_tasks
from eije_taskgraph import register as eije_taskgraph_register
from taskgraph.morph import register_morph
from taskgraph.parameters import extend_parameters_schema
from voluptuous import Optional
import json
import os

extend_parameters_schema({
    Optional("pull_request_number"): int,
    Optional("taskcluster_comment"): str,
    Optional("try_config"): str,
})

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

from . import optimize, target_tasks
from eije_taskgraph import register as eije_taskgraph_register
from taskgraph.morph import register_morph
import json

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

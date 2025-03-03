from taskgraph.util.schema import resolve_keyed_by
from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()

@transforms.add
def resolve_tasks_for(config, tasks):
    for task in tasks:
        resolve_keyed_by(task, "scopes", task['name'], **{ "tasks-for": config.params['tasks_for'] })
        resolve_keyed_by(task, "dependencies", task['name'], **{ "tasks-for": config.params['tasks_for'] })
        resolve_keyed_by(task, "fetches", task['name'], **{ "tasks-for": config.params['tasks_for'] })
        resolve_keyed_by(task, "worker.env", task['name'], **{ "tasks-for": config.params['tasks_for'] })
        yield task

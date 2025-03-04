import copy
from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()

@transforms.add
def generate_tasks(config, tasks):
    for task in tasks:
        new_task = copy.deepcopy(task)
        deps = new_task.setdefault("soft-dependencies", [])
        for dep in config.kind_dependencies_tasks:
            if dep not in deps:
                deps.append(dep)

        yield new_task

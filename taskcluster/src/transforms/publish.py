import copy
from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()

EXPECTATIONS_DEP = "make-expectations-patch-make-patch"

@transforms.add
def generate_tasks(config, tasks):
    pr_number = config.params.get("pull_request_number", -1)
    head_rev = config.params.get("head_rev", "")

    for task in tasks:
        new_task = copy.deepcopy(task)

        deps = new_task.setdefault("soft-dependencies", [])
        for dep in config.kind_dependencies_tasks:
            if dep not in deps:
                deps.append(dep)

        new_task["worker"]["pr-number"] = int(pr_number)
        new_task["worker"]["head-rev"] = head_rev

        attrs = new_task.setdefault("attributes", {})
        attrs["soft-payload"] = {
            EXPECTATIONS_DEP: "expectations-task",
        }

        yield new_task

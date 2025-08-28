from taskgraph.transforms.base import TransformSequence
import os

transforms = TransformSequence()

@transforms.add
def generate_tasks(config, tasks):
    pr_number = config.params.get("pull_request_number")
    if pr_number is None:
        yield from tasks
        return

    project = config.params.get('project', 'unknown').lower()

    for task in tasks:
        routes = task.setdefault("routes", [])
        routes.append("index.ap.{}.index.pr.{}.latest".format(project, pr_number))
        yield task


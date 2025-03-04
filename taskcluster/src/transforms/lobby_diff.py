from taskgraph.transforms.base import TransformSequence
import os

transforms = TransformSequence()

@transforms.add
def generate_tasks(config, tasks):
    pr_number = os.environ.get("ARCHIPELAGO_INDEX_PULL_REQUEST_NUMBER")
    if pr_number is None:
        yield from tasks
        return

    for task in tasks:
        routes = task.setdefault("routes", [])
        routes.append("index.ap.archipelago-index.index.pr.{}.latest".format(pr_number))
        yield task


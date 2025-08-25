from taskgraph.transforms.base import TransformSequence
import os

transforms = TransformSequence()

@transforms.add
def generate_tasks(config, tasks):
    pr_number = os.environ.get("GITHUB_PULL_REQUEST_NUMBER")
    if pr_number is None:
        yield from tasks
        return

    project = config.params.get('project', 'unknown').lower()

    for task in tasks:
        routes = task.setdefault("routes", [])
        routes.append("index.ap.{}.index.pr.{}.latest".format(project, pr_number))
        yield task


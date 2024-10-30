from taskgraph.transforms.base import TransformSequence
import os

transforms = TransformSequence()

@transforms.add
def generate_tasks(config, tasks):
    comment = os.environ.get("TASKCLUSTER_COMMENT")
    if comment not in ["diff"]:
        print("Not generating lobby diff tasks as it didn't come from a valid comment:", comment)
        return

    pr_number = os.environ.get("ARCHIPELAGO_INDEX_PULL_REQUEST_NUMBER")
    if pr_number is None:
        print("Not a PR, ignoring transform merge, graph will be incomplete. Set `ARCHIPELAGO_INDEX_PULL_REQUEST_NUMBER` to a valid PR number")
        return

    for task in tasks:
        routes = task.setdefault("routes", [])
        routes.append("index.ap.v2.archipelago-index.index.level-1.pr.{}.latest".format(pr_number))
        yield task


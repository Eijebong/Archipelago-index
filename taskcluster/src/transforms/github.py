from taskgraph.transforms.base import TransformSequence
import os

transforms = TransformSequence()

@transforms.add
def github_task(config, tasks):
    for task in tasks:
        env = task["worker"].setdefault("env", {})
        pr_number = str(os.environ.get("GITHUB_PULL_REQUEST_NUMBER", -1))
        env["GITHUB_PR"] = pr_number

        yield task

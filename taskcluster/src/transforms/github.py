from taskgraph.transforms.base import TransformSequence
import os

transforms = TransformSequence()

@transforms.add
def github_task(config, tasks):
    for task in tasks:
        env = task["worker"].setdefault("env", {})
        pr_number = str(config.params.get("pull_request_number", -1))
        env["GITHUB_PR"] = pr_number

        yield task

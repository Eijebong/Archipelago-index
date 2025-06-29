from taskgraph.transforms.base import TransformSequence
import os

transforms = TransformSequence()

@transforms.add
def add_comment_scopes(config, tasks):
    pr_number = str(os.environ.get("GITHUB_PULL_REQUEST_NUMBER", -1))
    project = config.params['project'].lower()
    for task in tasks:
        scopes = task.setdefault("scopes", [])
        if config.kind == "test-report":
            scopes.append(f"ap:github:action:create-aptest-comment-on-pr:{pr_number}")
        else:
            scopes.append(f"ap:github:action:create-apdiff-comment-on-pr:{pr_number}")
        scopes.append(f"ap:github:repo:{project}")
        yield task

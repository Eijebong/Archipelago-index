from taskgraph.transforms.base import TransformSequence
import os

transforms = TransformSequence()

@transforms.add
def github_task(config, tasks):
    for task in tasks:
        pr_number = str(os.environ.get("ARCHIPELAGO_INDEX_PULL_REQUEST_NUMBER", -1))

        task_for = config.params["tasks_for"]
        task_label = task['name']
        index_path = f"ap.archipelago-index.{task_label}.pr.{pr_number}.latest"

        # Re-use indexed PR tasks with comments
        if task_for == "github-issue-comment":
            opt = task.setdefault("optimization", {})
            skip_unless_changed = opt.pop("skip-unless-changed", [])
            task["optimization"] = {"skip-unless-changed-or-cached": {"index-path": [index_path], "skip-unless-changed": skip_unless_changed}}
        elif task_for.startswith("github-pull-request"):
            task.setdefault("routes", []).append(f"index.{index_path}")

        yield task

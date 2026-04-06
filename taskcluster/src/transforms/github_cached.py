from taskgraph.transforms.base import TransformSequence
import os

transforms = TransformSequence()

@transforms.add
def github_task(config, tasks):
    project = config.params.get('project', 'unknown').lower()

    for task in tasks:
        pr_number = config.params.get("pull_request_number", -1)

        task_for = config.params["tasks_for"]
        task_label = task['name']
        index_path = f"ap.{project}.pr.{task_label}.{pr_number}.latest"

        # Re-use indexed PR tasks with comments, unless the task opts out
        if task_for == "github-issue-comment" and not task.get("attributes", {}).get("always-rerun", False):
            opt = task.setdefault("optimization", {})
            skip_unless_changed = opt.pop("skip-unless-changed", [])
            task["optimization"] = {"skip-unless-changed-or-cached": {"index-path": [index_path], "skip-unless-changed": skip_unless_changed}}
        elif task_for.startswith("github-pull-request"):
            task.setdefault("routes", []).append(f"index.{index_path}")

        yield task

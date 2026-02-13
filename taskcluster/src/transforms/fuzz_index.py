from urllib.parse import quote

from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def fuzz_index(config, tasks):
    pr_number = config.params.get("pull_request_number")
    if not pr_number:
        yield from tasks
        return

    project = config.params['project'].lower()
    task_for = config.params["tasks_for"]

    for task in tasks:
        apworld_name = quote(task["attributes"]["apworld_name"], safe="")
        version = quote(task["attributes"]["version"], safe="")
        extra_args_key = task["attributes"].get("extra_args_key", "default")

        index_path = f"ap.{project}.fuzz.pr.{pr_number}.{apworld_name}.{version}.{extra_args_key}.latest"
        task["attributes"].setdefault("eager-index-routes", []).append(index_path)

        target_tasks_method = config.params.get("target_tasks_method")
        if task_for == "github-issue-comment" and target_tasks_method in ("r+", "r++"):
            opt = task.setdefault("optimization", {})
            skip_unless_changed = opt.pop("skip-unless-changed", [])
            task["optimization"] = {
                "skip-unless-changed-or-attempted": {
                    "index-path": [index_path],
                    "skip-unless-changed": skip_unless_changed
                }
            }

        yield task

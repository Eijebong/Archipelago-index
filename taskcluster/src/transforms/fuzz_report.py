from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def build_fuzz_report_payload(config, tasks):
    for task in tasks:
        fuzz_tasks = []
        for dep_label in task["dependencies"].values():
            dep_task = config.kind_dependencies_tasks[dep_label]
            extra_args_key = dep_task.attributes.get("extra_args_key", "default")
            fuzz_tasks.append({
                "task-id": {"task-reference": f"<{dep_label}>"},
                "extra-args": extra_args_key,
            })

        primary_dep = config.kind_dependencies_tasks[task["attributes"]["primary-dependency-label"]]
        apworld_name = primary_dep.attributes["apworld_name"]
        version = primary_dep.attributes["version"]

        task["label"] = f"fuzz-report-{apworld_name}-{version}"
        diff_label = "diff-index"
        task.setdefault("dependencies", {})[diff_label] = diff_label
        task.setdefault("soft-dependencies", []).append(diff_label)

        task["worker"]["fuzz-tasks"] = fuzz_tasks
        task["worker"]["diff-task"] = {"task-reference": f"<{diff_label}>"}
        task["worker"]["world-name"] = apworld_name
        task["worker"]["world-version"] = version

        yield task


@transforms.add
def add_fuzz_report_scopes(config, tasks):
    pr_number = config.params.get("pull_request_number", -1)
    project = config.params['project'].lower()

    for task in tasks:
        scopes = task.setdefault("scopes", [])
        scopes.append(f"ap:github:action:create-apfuzz-comment-on-pr:{pr_number}")
        scopes.append(f"ap:github:repo:{project}")
        yield task

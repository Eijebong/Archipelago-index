from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def build_upload_fuzz_payload(config, tasks):
    """Build worker payload for upload-fuzz-results tasks created by from_deps."""
    project = config.params['project'].lower()
    pr_number = config.params.get("pull_request_number", -1)
    comment = config.params.get("taskcluster_comment", "")
    is_test_fuzz = comment.startswith("test-fuzz") or comment.startswith("fuzz")

    for task in tasks:
        primary_dep = config.kind_dependencies_tasks[task["attributes"]["primary-dependency-label"]]
        apworld_name = primary_dep.attributes["apworld_name"]
        version = primary_dep.attributes["version"]
        extra_args_key = primary_dep.attributes.get("extra_args_key", "default")

        fuzz_task_label = primary_dep.label
        fuzz_report_label = f"fuzz-report-{apworld_name}-{version}"

        # For test-fuzz/fuzz: if-depend on fuzz-report (so upload happens after report)
        # For r+/r++: depend on publish-index (upload after publish succeeds)
        if is_test_fuzz:
            task.setdefault("dependencies", {})[fuzz_report_label] = fuzz_report_label
            task.setdefault("if-dependencies", []).append(fuzz_report_label)
        else:
            task.setdefault("dependencies", {})["publish-index"] = "publish-index"

        task["attributes"]["extra_args_key"] = extra_args_key
        task["attributes"]["is_test_fuzz"] = is_test_fuzz

        diff_label = "diff-index"
        task.setdefault("dependencies", {})[diff_label] = diff_label
        task.setdefault("soft-dependencies", []).append(diff_label)

        task["worker"]["fuzz-task"] = {"task-reference": f"<{fuzz_task_label}>"}
        task["worker"]["diff-task"] = {"task-reference": f"<{diff_label}>"}
        task["worker"]["world-name"] = apworld_name
        task["worker"]["world-version"] = version
        task["worker"]["extra-args"] = extra_args_key if extra_args_key != "default" else ""

        yield task


@transforms.add
def add_upload_fuzz_scopes(config, tasks):
    project = config.params['project'].lower()
    pr_number = config.params.get("pull_request_number", -1)

    for task in tasks:
        is_test_fuzz = task["attributes"].get("is_test_fuzz", False)
        scopes = task.setdefault("scopes", [])

        # For test-fuzz/fuzz: upload to PR, for r+/r++: upload to main
        if is_test_fuzz:
            scopes.append(f"ap:github:action:upload-fuzz-results:pr:{pr_number}")
        else:
            scopes.append("ap:github:action:upload-fuzz-results:branch:main")

        scopes.append(f"ap:github:repo:{project}")
        yield task

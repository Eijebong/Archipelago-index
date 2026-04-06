from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()

ALWAYS_RERUN_FOR_TARGETS = {"diff"}


@transforms.add
def remove_opt_if_hook(config, tasks):
    if config.params['tasks_for'] != 'rebuild-ap-worker':
        yield from tasks
        return

    for task in tasks:
        del task['optimization']
        yield task


@transforms.add
def mark_always_rerun(config, tasks):
    target = config.params.get("target_tasks_method", "")

    for task in tasks:
        if target in ALWAYS_RERUN_FOR_TARGETS:
            task.setdefault("attributes", {})["always-rerun"] = True
        yield task

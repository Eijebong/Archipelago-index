from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()

@transforms.add
def remove_opt_if_hook(config, tasks):
    if config.params['tasks_for'] != 'rebuild-ap-worker':
        yield from tasks
        return

    for task in tasks:
        del task['optimization']
        yield task

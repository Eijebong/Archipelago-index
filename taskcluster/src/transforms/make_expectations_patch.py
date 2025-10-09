from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()

@transforms.add
def add_all_expectations_deps(config, tasks):
    deps = [task for task in config.kind_dependencies_tasks.values() if task.attributes.get('latest')]
    for task in tasks:
        soft_deps = task.setdefault("soft-dependencies", [])
        soft_deps.extend((dep.label for dep in deps))

        attributes = task.setdefault("attributes", {})

        soft_fetches = attributes.setdefault("soft-fetches", {})
        # Something replaces spaces in artifact names with a `+`
        soft_fetches.update({dep.label: { "artifact": "public/test_results/{}.toml".format(dep.attributes['apworld_name'].replace(" ", "+")), "dest": "/builds/worker/checkouts/vcs/meta/"} for dep in deps})
        yield task


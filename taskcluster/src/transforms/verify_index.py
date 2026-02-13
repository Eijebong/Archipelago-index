from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()

@transforms.add
def verify_index(config, tasks):
    for task in tasks:
        if config.params["level"] == "3":
            routes = task.setdefault("routes", [])
            routes.append("notify.slack-channel.#12345.on-resolved")

        yield task

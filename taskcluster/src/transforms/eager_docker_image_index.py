from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def eager_docker_image_index(config, tasks):
    taskgraph_config = config.graph_config.get("taskgraph", {})
    cache_prefix = taskgraph_config.get(
        "cached-task-prefix", config.graph_config["trust-domain"]
    )
    level = config.params["level"]

    for task in tasks:
        cached = task.get("attributes", {}).get("cached_task")
        if cached:
            namespace = f"{cache_prefix}.cache.level-{level}.{cached['type']}.{cached['name']}.latest"
            task.setdefault("attributes", {}).setdefault(
                "eager-index-routes", []
            ).append(namespace)
        yield task

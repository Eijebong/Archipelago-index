from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def soft_docker_image(config, tasks):
    for task in tasks:
        if task.get("attributes", {}).get("soft-docker-image"):
            dep_label = task.get("dependencies", {}).pop("docker-image", None)
            if dep_label is not None:
                task.setdefault("soft-dependencies", []).append(dep_label)
                payload = task["task"]["payload"]
                payload["image"]["taskId"] = {"task-reference": f"<{dep_label}>"}
        yield task

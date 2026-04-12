from taskgraph.transforms.base import TransformSequence
from taskgraph.transforms.task import run_task_suffix

transforms = TransformSequence()


@transforms.add
def soft_docker_image(config, tasks):
    trust_domain = config.graph_config["trust-domain"]
    level = config.params["level"]
    cache_prefix = config.graph_config.get("taskgraph", {}).get(
        "cached-task-prefix", trust_domain
    )
    cache_name = f"{trust_domain}-level-{level}-checkouts-v3-{run_task_suffix()}"

    for task in tasks:
        if not task.get("attributes", {}).get("soft-docker-image"):
            yield task
            continue

        dep_label = task.get("dependencies", {}).pop("docker-image", None)
        if dep_label is None:
            yield task
            continue

        task.setdefault("soft-dependencies", []).append(dep_label)
        image_name = dep_label.removeprefix("docker-image-")

        td = task["task"]
        td["payload"]["image"] = {
            "path": "public/image.tar.zst",
            "namespace": f"{cache_prefix}.cache.level-{level}.docker-images.v2.{image_name}.latest",
            "type": "indexed-image",
        }

        td["payload"]["cache"] = {cache_name: "/builds/worker/checkouts"}
        td["scopes"].append(f"docker-worker:cache:{cache_name}")
        td["payload"]["env"]["TASKCLUSTER_CACHES"] = "/builds/worker/checkouts"

        yield task

from taskgraph.transforms.base import TransformSequence
import re

transforms = TransformSequence()


def _sanitize_index_path(component):
    return re.sub(r'[^a-zA-Z0-9_-]', lambda m: '~{:02x}'.format(ord(m.group())), component)


@transforms.add
def fetch_index(config, tasks):
    project = config.params['project'].lower()
    is_main = config.params.get('head_ref', '') == "refs/heads/main"

    for task in tasks:
        apworld_name = task["attributes"]["apworld_name"]
        version = task["attributes"]["version"]
        safe_name = _sanitize_index_path(apworld_name)
        safe_version = _sanitize_index_path(version)

        main_index_path = f"ap.{project}.world.{safe_name}.{safe_version}"

        if is_main:
            task.setdefault("routes", []).append(f"index.{main_index_path}")
            extra_index = task.setdefault("extra", {}).setdefault("index", {})
            extra_index["rank"] = "build_date"
            optimization_paths = [main_index_path]
        elif config.params.get('try_config'):
            try_index_path = f"ap.{project}.try.world.{safe_name}.{safe_version}"
            task.setdefault("routes", []).append(f"index.{try_index_path}")
            extra_index = task.setdefault("extra", {}).setdefault("index", {})
            extra_index["rank"] = "build_date"
            optimization_paths = [try_index_path, main_index_path]
        else:
            optimization_paths = [main_index_path]

        task["optimization"] = {
            "index-search": optimization_paths,
        }

        yield task

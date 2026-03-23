from taskgraph.transforms.base import TransformSequence
import re

transforms = TransformSequence()


def _sanitize_index_path(component):
    return re.sub(r'[^a-zA-Z0-9_-]', lambda m: '~{:02x}'.format(ord(m.group())), component)


@transforms.add
def fetch_index(config, tasks):
    project = config.params['project'].lower()
    head_ref = config.params.get('head_ref', '')
    is_main = head_ref in ('main', 'refs/heads/main')

    for task in tasks:
        apworld_name = task["attributes"]["apworld_name"]
        version = task["attributes"]["version"]
        safe_name = _sanitize_index_path(apworld_name)
        safe_version = _sanitize_index_path(version)

        if is_main:
            index_path = f"ap.{project}.world.{safe_name}.{safe_version}"
        else:
            index_path = f"ap.{project}.try.world.{safe_name}.{safe_version}"

        task.setdefault("routes", []).append(f"index.{index_path}")

        task["optimization"] = {
            "index-search": [index_path],
        }

        extra_index = task.setdefault("extra", {}).setdefault("index", {})
        extra_index["rank"] = "build_date"

        yield task

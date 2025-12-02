from taskgraph.transforms.base import TransformSequence
import argparse
import copy
import shlex
import os

transforms = TransformSequence()

parser = argparse.ArgumentParser(exit_on_error=False)
parser.add_argument("-r", "--runs", default=100, type=int)
parser.add_argument("-n", "--yamls_per_run", default="1", type=str)
parser.add_argument("--hook", default=None)
parser.add_argument("--skip-output", default=False, action='store_true')

@transforms.add
def fuzz_params(config, tasks):
    comment = config.params.get("taskcluster_comment", "")
    try_config = config.params.get("try_config", "")

    raw_params = None
    if comment.startswith("fuzz"):
        raw_params = comment.removeprefix("fuzz").strip()
    elif try_config:
        for line in try_config.splitlines():
            if line.startswith("fuzz "):
                raw_params = line.removeprefix("fuzz").strip()
                break

    dupe_with_empty = False
    if not raw_params:
        raw_params = "-r 5000 -n 1"
        dupe_with_empty = True

    args = parser.parse_args(shlex.split(raw_params))

    extra_args = ""
    if args.hook:
        extra_args += " --hook " + shlex.quote(args.hook)
    if args.skip_output:
        extra_args += " --skip-output"

    for task in tasks:
        env = task["worker"].setdefault("env", {})
        env["FUZZ_RUNS"] = str(args.runs)
        env["FUZZ_YAMLS_PER_RUN"] = str(args.yamls_per_run)
        env["FUZZ_EXTRA_ARGS"] = extra_args

        apworld_name = task["attributes"]["apworld_name"]
        version = task["attributes"]["version"]

        task.setdefault("attributes", {})["extra_args_key"] = "default"
        # Add combined attribute for grouping by apworld+version in fuzz-report
        task["attributes"]["apworld_version"] = f"{apworld_name}-{version}"

        yield copy.deepcopy(task)

        if dupe_with_empty:
            task["label"] = f"fuzz-no-restrictive-starts-{apworld_name}-{version}"
            task["attributes"]["extra_args_key"] = "no-restrictive-starts"

            env["FUZZ_EXTRA_ARGS"] = extra_args + "--hook hooks.with_empty:Hook"

            yield task

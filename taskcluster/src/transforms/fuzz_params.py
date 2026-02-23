from taskgraph.transforms.base import TransformSequence
import argparse
import shlex

transforms = TransformSequence()

parser = argparse.ArgumentParser(exit_on_error=False)
parser.add_argument("-r", "--runs", default=100, type=int)
parser.add_argument("-n", "--yamls_per_run", default="1", type=str)
parser.add_argument("--hook", default=None)
parser.add_argument("--skip-output", default=False, action='store_true')
parser.add_argument("--dump-ignored", default=False, action='store_true')

DEFAULT_FUZZ_PARAMS = "-r 5000 -n 1"


def extract_raw_fuzz_params(params):
    comment = params.get("taskcluster_comment", "")
    if comment.startswith("fuzz"):
        raw = comment.removeprefix("fuzz").strip()
        if raw:
            return raw

    try_config = params.get("try_config", "")
    if try_config:
        for line in try_config.splitlines():
            if line.startswith("fuzz "):
                raw = line.removeprefix("fuzz").strip()
                if raw:
                    return raw

    return None


@transforms.add
def fuzz_params(config, tasks):
    raw_params = extract_raw_fuzz_params(config.params) or DEFAULT_FUZZ_PARAMS
    args = parser.parse_args(shlex.split(raw_params))

    extra_args = ""
    if args.hook:
        extra_args += " --hook " + shlex.quote(args.hook)
    if args.skip_output:
        extra_args += " --skip-output"
    if args.dump_ignored:
        extra_args += " --dump-ignored"

    for task in tasks:
        env = task["worker"].setdefault("env", {})

        fuzz_runs = task.pop("fuzz-runs", None)
        env["FUZZ_RUNS"] = str(fuzz_runs if fuzz_runs is not None else args.runs)
        env["FUZZ_YAMLS_PER_RUN"] = str(args.yamls_per_run)

        task_extra_args = extra_args
        fuzz_hook = task.pop("fuzz-hook", None)
        if fuzz_hook:
            task_extra_args += " --hook " + fuzz_hook

        fuzz_extra_args = task.pop("fuzz-extra-args", None)
        if fuzz_extra_args:
            task_extra_args += " " + fuzz_extra_args

        env["FUZZ_EXTRA_ARGS"] = task_extra_args

        apworld_name = task["attributes"]["apworld_name"]
        version = task["attributes"]["version"]

        attributes = task.setdefault("attributes", {})
        attributes["apworld_version"] = f"{apworld_name}-{version}"

        is_fuzz_variant = task.pop("fuzz-variant", False)
        if is_fuzz_variant:
            attributes["fuzz-variant"] = True
            attributes["extra_args_key"] = task["name"]

        yield task

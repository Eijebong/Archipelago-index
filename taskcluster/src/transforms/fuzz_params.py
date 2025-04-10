from taskgraph.transforms.base import TransformSequence
import argparse
import shlex
import os

transforms = TransformSequence()

parser = argparse.ArgumentParser(exit_on_error=False)
parser.add_argument("-r", "--runs", default=100, type=int)
parser.add_argument("-n", "--yamls_per_run", default="1", type=str)
parser.add_argument("--classifier", default=None)
parser.add_argument("--skip-output", default=False, action='store_true')

@transforms.add
def fuzz_params(config, tasks):
    comment = os.environ.get("TASKCLUSTER_COMMENT", "")
    try_config = os.environ.get("TRY_CONFIG", "")

    raw_params = None
    if comment.startswith("fuzz"):
        raw_params = comment.removeprefix("fuzz").strip()
    elif try_config:
        for line in try_config.splitlines():
            if line.startswith("fuzz "):
                raw_params = line.removeprefix("fuzz").strip()
                break

    if raw_params is None:
        raw_params = "-r 100 -n 1"

    args = parser.parse_args(shlex.split(raw_params))

    extra_args = ""
    if args.classifier:
        extra_args += " --classifier " + shlex.quote(args.classifier)
    if args.skip_output:
        extra_args += " --skip-output"

    for task in tasks:
        env = task["worker"].setdefault("env", {})
        env["FUZZ_RUNS"] = str(args.runs)
        env["FUZZ_YAMLS_PER_RUN"] = str(args.yamls_per_run)
        env["FUZZ_EXTRA_ARGS"] = extra_args

        yield task

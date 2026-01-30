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
parser.add_argument("--dump-ignored", default=False, action='store_true')

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

    specific_fuzz = True
    if not raw_params:
        raw_params = "-r 5000 -n 1"
        specific_fuzz = False

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
        env["FUZZ_RUNS"] = str(args.runs)
        env["FUZZ_YAMLS_PER_RUN"] = str(args.yamls_per_run)
        env["FUZZ_EXTRA_ARGS"] = extra_args

        apworld_name = task["attributes"]["apworld_name"]
        version = task["attributes"]["version"]

        attributes = task.setdefault("attributes", {})
        # Add combined attribute for grouping by apworld+version in fuzz-report
        attributes["apworld_version"] = f"{apworld_name}-{version}"

        yield copy.deepcopy(task)

        # If we're not specifically fuzzing for something we want to run the full suite
        if not specific_fuzz:
            for (hook_name, hook) in (
                ("no-restrictive-starts", "hooks.with_empty:Hook"),
                ("check-ut", "worlds.tracker.fuzzer_hook:Hook"),
                ("check-gerpocalypse", "hooks.gerpocalypse:Hook"),
                ("check-item-location-count", "hooks.item_location_count:Hook"),
                ("check-lambda-capture", "hooks.detect_rule_variable_capture_issues:Hook"),
                ("check-placement-item-location-refs", "hooks.check_placement_item_location_references:Hook"),
                ("check-determinism", "hooks.determinism:Hook"),
            ):
                new_task = copy.deepcopy(task)
                new_task["label"] = f"fuzz-{hook_name}-{apworld_name}-{version}"
                new_task["attributes"]["extra_args_key"] = hook_name
                new_task["worker"]["env"]["FUZZ_EXTRA_ARGS"] = extra_args + "--hook " + hook

                # check-determinism is extra demanding, so tweak values a bit
                if hook_name == "check-determinism":
                    new_task["worker"]["env"]["FUZZ_EXTRA_ARGS"] += " -t 30 -j 4"
                if hook_name.startswith("check-"):
                    new_task["worker"]["env"]["FUZZ_RUNS"] = "500"


                yield new_task

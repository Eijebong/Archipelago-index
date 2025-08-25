import aplinter
import json
import sys
import subprocess
import os
import tempfile

if len(sys.argv) != 4:
    print("Usage: aplint_from_diff <diff_path> <index_path> <output_dir>")
    sys.exit(1)

index_path = sys.argv[2]
output = sys.argv[3]


def download_apworld(apworld, version, dest):
    subprocess.check_output(["apwm", "download", "-i", index_path, "-d", dest, "-p", f"{apworld}:{version}"])
    return os.path.join(dest, f"{apworld}-{version}.apworld")


for diff_file in os.scandir(sys.argv[1]):
    with open(diff_file) as fd:
        diff = json.load(fd)
        apworld_name = diff["apworld_name"]
        with tempfile.TemporaryDirectory() as dest:
            for version_diff in diff["diffs"]:
                _, version = version_diff.split('...')
                if not version:
                    continue
                file = download_apworld(apworld_name, version, dest)
                aplinter.lint(file, output)

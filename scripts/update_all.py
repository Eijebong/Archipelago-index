from pathlib import Path
from semver import Version

import argparse
import git # XXX: gitpython
import logging
import os
import re
import requests
import tomlkit # XXX: tomlkit
import semver # XXX: semver
from github import Auth, Github, GithubException # XXX: PyGithub

# Some apworlds have very old release with weird version numbers
BOGGY_TAGS = {
    "checksmate": [
        "v2023.10.28",
        "v2023.10.29",
        "v2023.11.01",
        "v2023.11.02",
        "v2023.11.04",
        "v2023.11.06",
        "v2023.11.10",
        "v2023.11.13",
        "v2023.11.16",
        "v2023.11.21",
        "v2023.11.25",
        "v2023.11.28",
        "v2023.11.29",
        "v2023.12.01",
    ],
    "apeescape": [
        "0.20",
    ],
    "ss": [
        "v0.5.0.1-pre",
        "v0.5.0.2-pre",
        "v0.5.0.3-pre",
        "v0.5.0.4-pre",
    ]
}

EXCLUDED_WORLDS = [
    "axiomverge", # Uses weird versioning, not worth trying
    "megamix", # Let repod handle those
    "pokemon_crystal", # Let James handle those
    "tevi", # Versioning too difficult to manage
    "ss", # Let harmjan deal with that
    "pokemon_frlg", # It's been in beta 1.0.0 forever which is not public ready
    "cvhodis", # Version in the index is wrong, don't care, it's not been updated for 6 months
    "sims4", # dev releasing non public version publicly, complaining about us updating to those
    "candybox2", # Weird versioning, not worth trying
]

logging.basicConfig(format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def infer_version_from_tag(tag_name):
    original_tag_name = tag_name

    tag_name = re.sub(r'.*?v?([0-9]+)\.([0-9]+)\.([0-9]+)(?:[\.\-_]([a-z0-9]+))?', r'\1.\2.\3-\4', tag_name, flags=re.IGNORECASE)

    try:
        version = Version.parse(tag_name, optional_minor_and_patch=True)
        return version
    except:
        pass

    tag_name = re.sub(r'.*?([0-9]+)\.([0-9]+)\.([0-9]+).*', r'\1.\2.\3', tag_name)
    try:
        version = Version.parse(tag_name, optional_minor_and_patch=True)
        return version
    except:
        pass

    # Try to extract major.minor version (e.g., "oos-12.4" -> "12.4")
    tag_name = re.sub(r'.*?([0-9]+)\.([0-9]+)(?:[^0-9].*)?$', r'\1.\2', original_tag_name)
    try:
        version = Version.parse(tag_name, optional_minor_and_patch=True)
        return version
    except:
        pass

    raise ValueError(f"Couldn't infer version from {original_tag_name}")


def test_infer_version():
    for (tag_name, expected) in (
        ("0.1.1", "0.1.1"),
        ("v0.1.2", "0.1.2"),
        ("FFTA2_0.0.9", "0.0.9"),
        ("0.2.0a", "0.2.0-a"),
        ("0.1", "0.1.0"),
        ("1.0", "1.0.0"),
        ("Spelunky2v0.1.1", "0.1.1"),
        ("0.4.1.1", "0.4.1-1"),
        ("alpha-0.3.3-rc1", "0.3.3-rc1"),
        ("v_0.2.0_beta", "0.2.0-beta"),
        ("v0.3.7.1", "0.3.7-1"),
        ("V0.5.10", "0.5.10"),
        ("V4.11.1", "4.11.1"),
        ("oos-12.4", "12.4.0"),
    ):
        assert infer_version_from_tag(tag_name) == Version.parse(expected, optional_minor_and_patch=True), (tag_name, expected, infer_version_from_tag(tag_name))

test_infer_version()

def bump_version(repo: git.Repo, apworld_name, latest_version, url, dry_run=False):
    if dry_run:
        return {
            'apworld': apworld_name,
            'version': str(latest_version),
            'custom_url': url,
            'status': 'would_update'
        }

    repo.head.reference = "main"
    repo.head.reset(index=True, working_tree=True)
    repo.heads.main.checkout()
    assert not repo.head.is_detached

    repo.create_head(apworld_name, "HEAD")
    repo.head.reference = apworld_name
    repo.head.reset(index=True, working_tree=True)
    repo.heads[apworld_name].checkout()

    assert not repo.head.is_detached

    with open(os.path.join(INDEX_ROOT, "index", f"{apworld_name}.toml"), "r") as fd:
        index = tomlkit.loads(fd.read())
        table = tomlkit.inline_table()
        if url is not None:
            table.append("url", url)
        index['versions'].append(str(latest_version), table)

    with open(os.path.join(TEMP_DIR, "index", f"{apworld_name}.toml"), "w") as fd:
        tomlkit.dump(index, fd)

    repo.index.add(os.path.join(TEMP_DIR, "index", f"{apworld_name}.toml"))
    repo.index.commit(f"Update {apworld_name} to {latest_version}")

    origin = repo.remote("origin")
    origin.fetch()
    branches = [branch.name for branch in repo.remotes.origin.refs]

    if apworld_name in branches:
        try:
            diff = repo.index.diff(f"origin/{apworld_name}", paths=[f"index/{apworld_name}.toml"])
        except:
            diff = []

        if not diff:
            logger.info("Empty diff with current origin, skipping push")
            return {
                'apworld': apworld_name,
                'version': str(latest_version),
                'custom_url': url,
                'status': 'no_diff'
            }

    logger.info(f"Pushing update for {apworld_name}")
    origin.push(apworld_name, force=True).raise_if_error()
    try:
        GITHUB_REPO.create_pull("main", apworld_name, title=f"Update {apworld_name}")
    except GithubException as e:
        pass

    try:
        GITHUB_REPO.get_pulls(state='open', head=f"Eijebong:{apworld_name}")[0].remove_from_labels('blocked by apworld')
    except:
        pass

    return {
        'apworld': apworld_name,
        'version': str(latest_version),
        'custom_url': url,
        'status': 'updated'
    }



def fetch_pred_apworlds():
    logger.info("Fetching current PRs")
    touched_apworlds = set()
    prs = GITHUB_REPO.get_pulls(state='open', sort='created', base='main')
    for pr in prs:
        if pr.user.login != "Eijebong":
            for file in pr.get_files():
                if file.filename.endswith('.toml'):
                    touched_apworlds.add(Path(file.filename).stem)

    return touched_apworlds

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
AUTH = Auth.Token(GITHUB_TOKEN)
GITHUB = Github(auth=AUTH)
GITHUB_REPO = GITHUB.get_repo("Eijebong/Archipelago-index")

INDEX_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../")
REPO_URL = "git@github.com:Eijebong/Archipelago-index.git"
TEMP_DIR = "/tmp/foo" # TODO: Make this an actual temp directory

parser = argparse.ArgumentParser(description='Update APWorld versions automatically')
parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
args = parser.parse_args()

if args.dry_run:
    logger.info("Running in DRY RUN mode - no changes will be made")

APWORLDS_TO_IGNORE = fetch_pred_apworlds() | set(EXCLUDED_WORLDS)
updates_made = []

if not args.dry_run:
    logger.info("Cloning repository")

    if not os.path.exists(TEMP_DIR):
        repo = git.Repo.init(TEMP_DIR)
        origin = repo.create_remote("origin", REPO_URL)
    else:
        # This is useful when testing with a set temp dir for speed
        repo = git.Repo(TEMP_DIR)
        origin = repo.remote("origin")

    origin.fetch("main")
    repo.head.reset("FETCH_HEAD", working_tree=True)
else:
    repo = None

logger.debug("Determining what to update")

for index_file in os.listdir(os.path.join(INDEX_ROOT, "index")):
    if not index_file.endswith('.toml'):
        continue
    apworld_name = Path(index_file).stem
    if apworld_name in APWORLDS_TO_IGNORE:
        logger.info(f"Ignoring {apworld_name} because someone already has a PR updating it")
        continue

    logger.info(f"Processing {apworld_name}")

    with open(os.path.join(INDEX_ROOT, "index", index_file), "rb") as fd:
        index = tomlkit.load(fd)
        logger.info("Checking {}".format(index["name"]))
        if index.get("disabled", False):
            logger.info("World is disabed, ignoring")
            continue

        url = "none"

        if "default_url" not in index:
            if "versions" in index:
                print(index['versions'])
                url = list(index['versions'].values())[-1].get('url', 'none')
        else:
            url = index['default_url']

        if 'github.com' in url and not 'raw/refs/' in url:
            repository = url.split('/releases/download')[0][len('https://github.com/'):]
        else:
            logger.debug("Default URL `{}` isn't a github release, this is not supported".format(url))
            continue


        logger.debug("Fetching latest release for {}".format(apworld_name))
        git_repo = GITHUB.get_repo(repository)
        releases = git_repo.get_releases()

        current_latest = [Version.parse(v) for v in index["versions"].keys()]
        current_latest = max(Version.parse(v) for v in index["versions"].keys())
        original_latest = current_latest
        logger.debug(f"Current latest is {current_latest}")
        custom_url = False

        for release in releases:
            tag_name = release.tag_name
            if tag_name in BOGGY_TAGS.get(apworld_name, []):
                logger.debug(f"Ignoring boggy tag: {tag_name}")
                continue
            try:
                version = infer_version_from_tag(tag_name)
            except ValueError:
                logger.warning(f"Unable to get version from {tag_name}. Ignoring it")
                continue

            has_apworld = False
            for asset in release.assets:
                if asset.name == f"{apworld_name}.apworld":
                    has_apworld = True
                    break

            if has_apworld and version > current_latest:
                current_latest = version
                if index.get("default_url", "").replace("{{version}}", str(version)) != asset.browser_download_url:
                    custom_url = asset.browser_download_url
                else:
                    custom_url = None

        if current_latest > original_latest:
            logger.info(f"Found a newer release for {apworld_name}. Version {current_latest} is greather than the current {original_latest}")
            result = bump_version(repo, apworld_name, current_latest, custom_url, args.dry_run)
            if result:
                result['old_version'] = str(original_latest)
                updates_made.append(result)
            continue

# Print summary
logger.info("\n" + "="*50)
if args.dry_run:
    logger.info("DRY RUN SUMMARY")
else:
    logger.info("UPDATE SUMMARY")
logger.info("="*50)

if not updates_made:
    logger.info("No updates found.")
else:
    for update in updates_made:
        status_msg = {
            'would_update': '[WOULD UPDATE]',
            'updated': '[UPDATED]',
            'no_diff': '[NO DIFF]'
        }.get(update['status'], f"[{update['status'].upper()}]")

        logger.info(f"{status_msg} {update['apworld']}: {update['old_version']} -> {update['version']}")
        if update['custom_url']:
            logger.info(f"    Custom URL: {update['custom_url']}")

logger.info(f"\nTotal: {len(updates_made)} APWorlds processed")


from pathlib import Path
from semver import Version

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
    ]
}

EXCLUDED_WORLDS = [
    "megamix", # Let repod handle those
]

logging.basicConfig(format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def infer_version_from_tag(tag_name):
    original_tag_name = tag_name

    tag_name = re.sub(r'.*v?([0-9]+)\.([0-9]+)\.([0-9]+)[\.\-_]?([a-z0-9]+)', r'\1.\2.\3-\4', tag_name)

    try:
        version = Version.parse(tag_name, optional_minor_and_patch=True)
        return version
    except:
        pass

    tag_name = re.sub(r'.*([0-9]+)\.([0-9]+)\.([0-9]+).*', r'\1.\2.\3', tag_name)
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
    ):
        assert infer_version_from_tag(tag_name) == Version.parse(expected, optional_minor_and_patch=True)

test_infer_version()

def bump_version(repo: git.Repo, apworld_name, latest_version, url):
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
    origin.fetch(apworld_name)
    try:
        diff = repo.index.diff(f"origin/{apworld_name}", paths=[f"index/{apworld_name}.toml"])
    except:
        diff = []

    if not diff:
        logger.info("Empty diff with current origin, skipping push")
        return

    logger.info(f"Pushing update for {apworld_name}")
    origin.push(apworld_name, force=True).raise_if_error()
    try:
        GITHUB_REPO.create_pull("main", apworld_name, title=f"Update {apworld_name}")
    except GithubException as e:
        pass


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

APWORLDS_TO_IGNORE = fetch_pred_apworlds() | set(EXCLUDED_WORLDS)
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

logger.debug("Determining what to update")

for index_file in os.listdir(os.path.join(INDEX_ROOT, "index")):
    apworld_name = Path(index_file).stem
    if apworld_name in APWORLDS_TO_IGNORE:
        logger.info(f"Ignoring {apworld_name} because someone already has a PR updating it")
        continue

    with open(os.path.join(INDEX_ROOT, "index", index_file), "rb") as fd:
        index = tomlkit.load(fd)
        logger.info("Checking {}".format(index["name"]))
        if index.get("disabled", False):
            logger.info("World is disabed, ignoring")
            continue
        if "default_url" not in index:
            logger.debug("No default url, skipping")
            continue

        if 'github.com' in index['default_url'] and not 'raw/refs/' in index['default_url']:
            repository = index["default_url"].split('/releases/download')[0][len('https://github.com/'):]
        else:
            logger.debug("Default URL {} isn't a github release, this is not supported".format(index['default_url']))
            continue


        logger.debug("Fetching latest release for {}".format(apworld_name))
        git_repo = GITHUB.get_repo(repository)
        releases = git_repo.get_releases()

        current_latest = print([Version.parse(v) for v in index["versions"].keys()])
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
                if index["default_url"].replace("{{version}}", str(version)) != asset.browser_download_url:
                    custom_url = asset.browser_download_url
                else:
                    custom_url = None

        if current_latest > original_latest:
            logger.info(f"Found a newer release for {apworld_name}. Version {current_latest} is greather than the current {original_latest}")
            bump_version(repo, apworld_name, current_latest, custom_url)
            continue


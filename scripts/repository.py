import os
import requests
import logging
from config import config, log, console, args
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
import json

from repo_types import RepoManifest

progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
    console=console,
)


def check_if_cache_folder_exist():
    if not os.path.exists(".cache"):
        os.makedirs(".cache")


requests_log = logging.getLogger("urllib3.connectionpool")
requests_log.setLevel(logging.WARNING)


def add_repository(url: str):
    if not url.endswith("/"):
        url += "/"
    if not url.endswith("manifest.json"):
        url += "manifest.json"
    log.info(f"Adding repo {url}")
    response = requests.get(url)
    if response.status_code != 200:
        log.error(f"failed to add repo {url}, got response code {response.status_code}")
        exit(1)
    manifest: RepoManifest = response.json()

    if os.path.exists(os.path.join(".cache", manifest["repo"]["uuid"])):
        log.error(
            f"Repository {url}, already exists, if you want to update it, run `patcher.py --repo-update`"
        )
        exit(1)

    os.makedirs(os.path.join(".cache", manifest["repo"]["uuid"]))
    with open(
        os.path.join(".cache", manifest["repo"]["uuid"], "manifest.json"),
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(manifest, file, indent=4, ensure_ascii=False)

    with open(args.config, "w", encoding="utf-8") as file:
        config["repositories"].append(
            {
                "title": manifest["repo"]["title"],
                "uuid": manifest["repo"]["uuid"],
                "url": url,
            }
        )
        json.dump(config, file, indent=4, ensure_ascii=False)

    log.info(
        f"repo `{manifest['repo']['title']}` added, run `patcher.py --repo-update` to fetch latest patches"
    )


def fetch_repositories():
    with console.status("[bold green]fetching repositories[/bold green]") as status:
        for repo in config["repositories"]:
            log.info(f"Updating repo: {repo['title']}")
            response = requests.get(repo["url"])
            if response.status_code != 200:
                log.error(
                    f"failed to update repo {repo['title']}, got response code {response.status_code}"
                )
                continue

            old_manifest: RepoManifest = {}
            with open(
                os.path.join(".cache", manifest["repo"]["uuid"], "manifest.json"),
                "r",
                encoding="utf-8",
            ) as file:
                old_manifest = json.load(manifest, file, indent=4, ensure_ascii=False)

            manifest: RepoManifest = response.json()
            with open(
                os.path.join(".cache", manifest["repo"]["uuid"], "manifest.json"),
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(manifest, file, indent=4, ensure_ascii=False)

            patches_path = os.path.join(".cache", manifest["repo"]["uuid"], "patches")
            repo_base = repo["url"].removesuffix("manifest.json")
            os.makedirs(patches_path, exist_ok=True)
            for patch in manifest["patches"]:
                existing_patch = next(
                    (
                        p
                        for p in old_manifest["patches"]
                        if p.get('uuid') == patch.get('uuid')
                    ),
                    None,
                )

                if not existing_patch or existing_patch.get('modDate') != patch.get('modDate'):
                    response = requests.get(f"{repo_base}/patches/{patch['filename']}")
                    if response.status_code != 200:
                        log.error(
                            f"failed get patch {patch['filename']} from repo {repo['title']}, got response code {response.status_code}"
                        )
                        continue

                    with open(os.path.join(patches_path, patch["filename"]), "wb") as file:
                        for bytes in response.iter_content(chunk_size=32768):
                            file.write(bytes)

                        log.info(f"Updated patch: {patch['title']} ({patch['filename']})")

            log.info(f"Updated repo: {repo['title']}")

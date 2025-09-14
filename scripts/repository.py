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

from repo_types import RepoManifest, PatchMetaData, ResourceMetaData

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
    if not os.path.exists("repos"):
        os.makedirs("repos")


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

    repo_path = os.path.join("repos", manifest["repo"]["uuid"].replace("-", "_"))
    if os.path.exists(repo_path):
        log.error(
            f"Repository {url}, already exists, if you want to update it, run `patcher.py --repo-update`"
        )
        exit(1)

    os.makedirs(repo_path)
    with open(
        os.path.join(repo_path, "manifest.json"),
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


def load_manifest(repo_path: str) -> RepoManifest:
    with open(
        os.path.join(repo_path, "manifest.json"),
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_manifest(repo_path: str, manifest: RepoManifest):
    with open(
        os.path.join(repo_path, "manifest.json"),
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(manifest, file, indent=4, ensure_ascii=False)


def download_file(url: str, path: str, name: str):
    log.info(f"Requesting {url}")
    response = requests.get(url, stream=True)
    total = int(response.headers.get("content-length", None))
    task_id = progress.add_task(
        f"download-{name}", start=False, total=total, filename=name
    )

    if response.status_code != 200:
        log.error(
            f"Failed to download {name}, got response code {response.status_code}"
        )
        return

    with open(path, "wb") as file:
        progress.start_task(task_id)
        for bytes in response.iter_content(chunk_size=32768):
            size = file.write(bytes)
            progress.update(task_id, advance=size)


def download_patch(url: str, repo: RepoManifest, patch: PatchMetaData):
    download_file(
        url,
        os.path.join(
            "repos",
            repo["repo"]["uuid"].replace("-", "_"),
            "patches",
            patch["filename"],
        ),
        patch["filename"],
    )


def download_resource(url: str, repo: RepoManifest, resource: ResourceMetaData):
    download_file(
        url,
        os.path.join(
            "repos",
            repo["repo"]["uuid"].replace("-", "_"),
            "resources",
            resource["filename"],
        ),
        resource["filename"],
    )


def fetch_repositories():
    with console.status("[bold green]fetching repositories[/bold green]") as status:
        status.start()
        for repo in config["repositories"]:
            repo_path = os.path.join("repos", repo["uuid"].replace("-", "_"))
            patches_path = os.path.join(repo_path, "patches")
            resources_path = os.path.join(repo_path, "resources")

            os.makedirs(repo_path, exist_ok=True)
            os.makedirs(patches_path, exist_ok=True)
            os.makedirs(resources_path, exist_ok=True)

            log.info(f"Updating repo: `{repo['title']}`")
            try:
                response = requests.get(repo["url"])
                if response.status_code != 200:
                    log.error(
                        f"failed to update repo `{repo['title']}`, got response code {response.status_code}"
                    )
                    continue
            except requests.exceptions.RequestException as e:
                log.error(f"failed to update repo `{repo['title']}`, {e}")
                continue

            old_manifest = load_manifest(repo_path)
            new_manifest: RepoManifest = response.json()
            repo_base_url = repo["url"].removesuffix("manifest.json").removesuffix("/")

            if not os.path.exists(os.path.join(patches_path, "__init__.py")):
                with open(
                    os.path.join(patches_path, "__init__.py"), "w", encoding="utf-8"
                ) as file:
                    file.write("")

            with progress:
                progress.start()
                for patch in new_manifest["patches"]:
                    existing_patch = next(
                        (
                            p
                            for p in old_manifest["patches"]
                            if p.get("uuid") == patch.get("uuid")
                        ),
                        None,
                    )
                    if (
                        not existing_patch
                        or existing_patch.get("sha256") != patch.get("sha256")
                        or not os.path.exists(
                            os.path.join(patches_path, patch["filename"])
                        )
                    ):
                        download_patch(
                            f"{repo_base_url}/patches/{patch['filename']}",
                            new_manifest,
                            patch,
                        )
                for resource in new_manifest["resources"]:
                    existing_resource = next(
                        (
                            p
                            for p in old_manifest["resources"]
                            if p.get("filename") == resource.get("filename")
                        ),
                        None,
                    )
                    if (
                        not existing_resource
                        or existing_resource.get("sha256") != resource.get("sha256")
                        or not os.path.exists(
                            os.path.join(resources_path, resource["filename"])
                        )
                    ):
                        download_resource(
                            f"{repo_base_url}/resources/{resource['filename']}",
                            new_manifest,
                            resource,
                        )
                progress.stop()

            save_manifest(repo_path, new_manifest)
            log.info(f"Updated repo: {repo['title']}")
        status.stop()

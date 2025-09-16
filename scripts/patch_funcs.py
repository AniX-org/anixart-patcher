import importlib
import json
from typing import TypedDict
from repo_types import PatchMetaData, RepoManifest
from config import config, log
from beaupy import select_multiple
from rich.progress import BarColumn, Progress, TextColumn
import os


class Patch:
    def __init__(self, name, pkg):
        self.name = name
        self.package = pkg
        self.applied = False

    def apply(self, settings: dict, globals: dict) -> bool:
        try:
            self.applied = self.package.apply(settings, globals)
            return True
        except Exception as e:
            log.error(
                f"error while applying a patch {self.name}: %s, with args: %s",
                e,
                e.args,
                exc_info=True,
            )
            return False


def get_patch_list_from_repo(repo_uuid: str) -> list[PatchMetaData]:
    manifest_patches = json.load(
        open(
            f"repos/{repo_uuid.replace("-", "_")}/manifest.json",
            "r",
            encoding="utf-8",
        )
    )["patches"]
    patch_files = os.listdir(f"repos/{repo_uuid.replace('-', '_')}/patches") or []
    existing_patches = [p for p in manifest_patches if p["filename"] in patch_files]
    return sorted(existing_patches, key=lambda x: x["title"])


def find_patch_in_repo(repo_uuid: str, title: str) -> PatchMetaData:
    return next(
        (p for p in get_patch_list_from_repo(repo_uuid) if p["title"] == title), None
    )


def sort_patches_by_priority(patches: list[PatchMetaData]) -> list[PatchMetaData]:
    return sorted(patches, key=lambda x: x["priority"])


def select_patches_from_repo(repo_uuid: str) -> list[PatchMetaData]:
    return select_multiple(
        get_patch_list_from_repo(repo_uuid),
        preprocessor=lambda x: x["title"],
        tick_character="X",
    )


progress = Progress(
    "[progress.description]{task.description}",
    TextColumn(text_format="{task.fields[patch]}"),
    BarColumn(bar_width=None),
    "[blue]{task.completed}/{task.total}",
)


class PatchStatus(TypedDict):
    name: str
    uuid: str
    status: bool


class PatchGlobals(TypedDict):
    apk: str
    app_version_name: str
    app_version_code: int
    app_sdk_version_min: int
    app_sdk_version_max: int
    patches_enabled: list[PatchMetaData]
    patches_statuses: list[PatchStatus]


def apply_patches_from_repo(
    repo_uuid: str, patches: list[PatchMetaData], globals: PatchGlobals
) -> tuple[RepoManifest, list[PatchStatus]]:
    statuses: list[PatchStatus] = []
    patches = sort_patches_by_priority(patches)

    manifest: RepoManifest = json.load(
        open(
            f"repos/{repo_uuid.replace("-", "_")}/manifest.json", "r", encoding="utf-8"
        )
    )

    globals["patches_enabled"].extend(patches)
    with progress:
        task = progress.add_task(
            f"applying patches from {manifest['repo']['title']}:",
            total=len(patches),
            patch="",
        )
        for patch in patches:
            progress.update(task, patch=patch["title"])
            module = importlib.import_module(
                f"repos.{repo_uuid.replace("-", "_")}.patches.{patch['filename'][:-3]}"
            )
            status = module.apply(patch["settings"], globals)
            statuses.append(
                {"name": patch["title"], "uuid": patch["uuid"], "status": status}
            )
            globals["patches_statuses"].append(
                {"name": patch["title"], "uuid": patch["uuid"], "status": status}
            )
            progress.update(task, advance=1)

        progress.update(task, description="patches applied", patch="")

    return manifest, statuses


def select_and_apply_patches(globals: PatchGlobals) -> list[PatchStatus]:
    toApply: dict[str, list[PatchMetaData]] = {}
    statuses = []

    for repo in config["repositories"]:
        if not os.path.exists(
            f"repos/{repo['uuid'].replace("-", "_")}/patches/__init__.py"
        ):
            continue
        patches = select_patches_from_repo(repo["uuid"])
        if len(patches) == 0:
            continue
        toApply[repo["uuid"]] = patches

    if len(toApply) == 0:
        return []

    for repo, patches in toApply.items():
        manifest, patchStatuses = apply_patches_from_repo(repo, patches, globals)
        statuses.extend(patchStatuses)

    return statuses

import json
from repo_types import PatchMetaData, RepoManifest
from config import config, log
from beaupy import select_multiple


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


def get_patch_list() -> list[PatchMetaData]:
    patches: list[PatchMetaData] = []

    for repo in config["repositories"]:
        manifest: RepoManifest = json.load(
            open(f"repos/{repo['uuid']}/manifest.json", "r", encoding="utf-8")
        )
        patches.extend(manifest["patches"])

    return sorted(patches, key=lambda x: x["title"])


def find_patch(title: str) -> PatchMetaData:
    return next((p for p in get_patch_list() if p["title"] == title), None)


def sort_patches_by_priority(patches: list[PatchMetaData]) -> list[PatchMetaData]:
    return sorted(patches, key=lambda x: x["priority"])


def select_patches() -> list[PatchMetaData]:
    return select_multiple(
        get_patch_list(), preprocessor=lambda x: x["title"], tick_character="X"
    )


def apply_patches(patches: list[PatchMetaData], conf: dict) -> bool:
    pass
    # return all(patch.apply(conf) for patch in patches)

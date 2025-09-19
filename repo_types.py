from typing import TypedDict, NotRequired, Any


class RepoConfig(TypedDict):
    title: str
    url: str
    initDate: str
    modDate: str
    uuid: str


class RepoMaintainerConfig(TypedDict):
    maintainer: str
    url: str


class PatchMetaData(TypedDict):
    filename: str
    title: str
    description: str
    author: str
    readme: str
    version: str
    initDate: str
    modDate: str
    uuid: str
    sha256: str
    priority: int
    tags: list[str]
    settings: NotRequired[dict[str, Any]]


class ResourceMetaData(TypedDict):
    filename: str
    directory: str
    sha256: str


class RepoManifest(TypedDict):
    repo: RepoConfig
    maintainer: RepoMaintainerConfig
    patches: list[PatchMetaData]
    resources: list[ResourceMetaData]


PatchTags: list[str] = ["UI", "Code", "undefined"]

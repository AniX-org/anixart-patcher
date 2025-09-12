import argparse
import json
import logging
import os
from typing import TypedDict
from rich.logging import RichHandler
from rich.console import Console


FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger("rich")
console = Console()

parser = argparse.ArgumentParser(prog="anixart patcher")
parser.add_argument("--config", help="path to config.json file", default="config.json")
parser.add_argument("--no-decompile", action="store_true")
parser.add_argument("--no-compile", action="store_true")
parser.add_argument("--repo-add", help="add a new repo to config.json file", type=str, default=None)
parser.add_argument("--repo-update", help="fetch latest version of all repos", action="store_true")
parser.add_argument("--apk", help="apk file name to patch", type=str, default=None)
args = parser.parse_args()


class ConfigTools(TypedDict):
    tool: str
    url: str


class ConfigFolders(TypedDict):
    tools: str
    apks: str
    decompiled: str
    out: str


class ConfigXmlNS(TypedDict):
    android: str
    app: str


class RepoList(TypedDict):
    title: str
    url: str
    uuid: str

class ScriptConfig(TypedDict):
    log_level: str
    repositories: list[RepoList]
    tools: list[ConfigTools]
    folders: ConfigFolders
    xml_ns: ConfigXmlNS


def load_config() -> ScriptConfig:
    config = None

    if not os.path.exists(args.config):
        log.exception("file `config.json` is not found!")
        exit(1)

    with open(args.config, "r", encoding="utf-8") as file:
        config = json.loads(file.read())

    log.setLevel(config.get("log_level", "NOTSET").upper())

    return config


config = load_config()

import os
import requests
import logging
from config import config, log, console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

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
    console=console
)


def check_if_tools_folder_exist():
    if not os.path.exists(config["folders"]["tools"]):
        log.info(f"creating `tools` folder: {config['folders']['tools']}")
        os.makedirs(config["folders"]["tools"])


def check_if_tool_exists(tool: str) -> bool:
    if not os.path.exists(f"{config['folders']['tools']}/{tool}"):
        return False
    elif os.path.exists(f"{config['folders']['tools']}/{tool}") and os.path.isdir(
        f"{config['folders']['tools']}/{tool}"
    ):
        log.warning(f"`{config['folders']['tools']}/{tool}` is a folder")
        return True
    else:
        return True


requests_log = logging.getLogger("urllib3.connectionpool")
requests_log.setLevel(logging.WARNING)


def prepare_download_tool(url: str, tool: str):
    if check_if_tool_exists(tool):
        return

    progress.start()
    try:
        download_tool(url, tool)
    except Exception as e:
        log.error(f"error while downloading `{tool}`: {e}")
    finally:
        progress.stop()

def download_tool(url, tool):
    log.info(f"Requesting {url}")
    response = requests.get(url, stream=True)
    total = int(response.headers.get("content-length", None))
    task_id = progress.add_task(f"download-{tool}", start=False, total=total, filename=tool)

    with open(f"{config['folders']['tools']}/{tool}", "wb") as file:
        progress.start_task(task_id)
        for bytes in response.iter_content(chunk_size=32768):
            size = file.write(bytes)
            progress.update(task_id, advance=size)
    progress.remove_task(task_id)

    if os.name == "posix":
        os.chmod(f"{config['folders']['tools']}/{tool}", 0o744)

def check_and_download_all_tools():
    check_if_tools_folder_exist()
    for tool in config["tools"]:
        if os.name in tool["os"]:
            prepare_download_tool(tool["url"], tool["tool"])
            log.info(f"`{tool["tool"]}` downloaded")
    log.info("all tools downloaded")
import subprocess
from config import log, config, console
from beaupy import select
import os


def check_java_version():
    command = ["java", "-version"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        version_line = result.stderr.splitlines()[0]
        if all(f"{i}." not in version_line for i in range(8, 100)):
            log.error("java 8+ is not installed")
            exit(1)
    except subprocess.CalledProcessError:
        log.error("java 8+ is not found")
        exit(1)
    log.info(f"found java: {version_line}")


def run_cmd(cmd: list[str]):
    try:
        subprocess.run(cmd, shell=True, check=True, text=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        log.fatal(
            "error of running a command: %s :: %s",
            " ".join(cmd),
            e.stderr,
            exc_info=True,
        )
        exit(1)


def decompile_apk(apk_path: str):
    run_cmd(
        f"java -jar {config['folders']['tools']}/apktool.jar d -f -o {config['folders']['decompiled']} {apk_path}"
    )


def compile_apk(apk_path: str):
    run_cmd(
        f"java -jar {config['folders']['tools']}/apktool.jar b -f -o {apk_path} {config['folders']['decompiled']}"
    )


def list_apks():
    apks = []
    if not os.path.exists(config["folders"]["apks"]):
        log.info(f"creating `apks` folder: {config['folders']['apks']}")
        os.mkdir(config["folders"]["apks"])
        return apks

    apks.extend(
        file
        for file in os.listdir(config["folders"]["apks"])
        if file.endswith(".apk")
        and os.path.isfile(f"{config['folders']['apks']}/{file}")
    )
    return apks


def select_apk(apks: list[str]) -> str:
    if not apks:
        log.info("no apks found")
        exit(0)

    console.print("select apk file to patch")
    apks.append("cancel")
    apk = select(apks, cursor="->", cursor_style="cyan")
    if not apk or apk == "cancel":
        log.info("patching cancelled")
        exit(0)
    return apk

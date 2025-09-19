import subprocess
from config import log, config, console
from beaupy import select
import os
import yaml
from lxml import etree


def check_java_version() -> None:
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


def run_cmd(cmd: list[str], ignore_error: bool = False) -> bool | None:
    try:
        subprocess.run(cmd, shell=True, check=True, text=True, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        if not ignore_error:
            log.fatal(
                "error of running a command: %s :: %s",
                " ".join(cmd),
                e.stderr,
                exc_info=True,
            )
            exit(1)
        else:
            log.error(
                "error of running a command: %s :: %s",
                " ".join(cmd),
                e.stderr,
                exc_info=True,
            )
            return False


def decompile_apk(apk_path: str) -> None:
    run_cmd(
        f"java -jar {config['folders']['tools']}/apktool.jar d -f -o {config['folders']['decompiled']} {apk_path}"
    )


def compile_apk(apk_path: str) -> None:
    run_cmd(
        f"java -jar {config['folders']['tools']}/apktool.jar b -f -o {apk_path} {config['folders']['decompiled']}"
    )


def sign_apk(apk_path: str) -> None:
    apk_aligned_path = apk_path.replace(".apk", "-aligned.apk")
    apk_signed_path = apk_path.replace(".apk", "-aligned-signed.apk")
    if os.name == "nt":
        run_cmd(
            f"{config['folders']['tools']}/zipalign.exe -v 4 {apk_path} {apk_aligned_path}"
        )
    elif os.name == "posix":
        run_cmd(
            f"{config['folders']['tools']}/zipalign -p 4 {apk_path} {apk_aligned_path}"
        )
    else:
        log.fatal("os not supported: %s", os.name)
        exit(1)

    cmd = f"java -jar {config['folders']['tools']}/apksigner.jar \
        sign --v1-signing-enabled false --v2-signing-enabled true --v3-signing-enabled true"
    cmd += f" --ks {os.getenv("KEYSTORE_PATH", "keystore.jks")}"
    if os.getenv("KEYSTORE_PASS"):
        cmd += f" --ks-pass env:KEYSTORE_PASS"
    if os.getenv("KEYSTORE_KEY_ALIAS"):
        cmd += f" --ks-key-alias {os.getenv('KEYSTORE_KEY_ALIAS')}"
    if os.getenv("KEYSTORE_KEY_PASSWORD"):
        cmd += f" --key-pass pass:{os.getenv('KEYSTORE_KEY_PASSWORD')}"
    cmd += f" --out {apk_signed_path} {apk_aligned_path}"
    run_cmd(cmd)


def list_apks() -> list[str]:
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


def read_apktool_yml() -> tuple[str, int, int, int]:
    with open(
        f"{config['folders']['decompiled']}/apktool.yml", "r", encoding="utf-8"
    ) as f:
        data = yaml.load(f.read(), Loader=yaml.Loader)
        versionName = data.get("versionInfo").get("versionName", "None")
        versionCode = data.get("versionInfo").get("versionCode", 0)
        minSdkVersion = data.get("sdkInfo").get("minSdkVersion", 0)
        targetSdkVersion = data.get("sdkInfo").get("targetSdkVersion", 0)

    return versionName, versionCode, minSdkVersion, targetSdkVersion


def save_apktool_yml(
    versionName: str, versionCode: int, minSdkVersion: int, targetSdkVersion: int
) -> None:
    data = None
    apktool_yml_path = f"{config['folders']['decompiled']}/apktool.yml"

    with open(apktool_yml_path, "r", encoding="utf-8") as f:
        data = yaml.load(f.read(), Loader=yaml.Loader)

    sdkInfo = {
        "minSdkVersion": minSdkVersion,
        "targetSdkVersion": targetSdkVersion,
    }
    versionInfo = {
        "versionName": versionName,
        "versionCode": versionCode,
    }
    data.update(
        {
            "sdkInfo": sdkInfo,
            "versionInfo": versionInfo,
        }
    )

    with open(apktool_yml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, indent=2, Dumper=yaml.Dumper)


def set_color(name: str, value: str, root) -> None:
    for element in root:
        if element.tag == "color" and element.attrib.get("name", None) == name:
            element.text = value
            break


def change_colors(values: dict[str, str]) -> None:
    file_path = f"{config['folders']['decompiled']}/res/values/colors.xml"
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(file_path, parser)
    root = tree.getroot()
    for value in values.items():
        set_color(value[0], value[1], root)
    tree.write(
        file_path,
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8",
    )

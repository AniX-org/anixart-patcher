from scripts.download_tools import check_and_download_all_tools
from scripts.patch_funcs import PatchGlobals, print_patches, select_and_apply_patches
from scripts.repository import add_repository, fetch_repositories
from scripts.utils import (
    check_java_version,
    compile_apk,
    decompile_apk,
    list_apks,
    read_apktool_yml,
    select_apk,
    sign_apk,
)
from config import args, config, log
from beaupy import confirm
import shutil
import os

if __name__ == "__main__":
    if args.repo_add:
        add_repository(args.repo_add)
        exit(0)
    if args.repo_update:
        fetch_repositories()
        exit(0)
    if args.sign_only:
        outs = os.listdir(config["folders"]["out"])
        for out in outs:
            if out.endswith("-patched.apk"):
                sign_apk(f"{config['folders']['out']}/{out}")
            else:
                os.remove(f"{config['folders']['out']}/{out}")
        exit(0)
    if args.list:
        print_patches()
        exit(0)

    check_and_download_all_tools()
    check_java_version()

    apk = args.apk or select_apk(list_apks())
    log.info(f"selected apk: {apk}")

    if not args.no_decompile:
        log.info("Decompile APK")
        decompile_apk(f"{config['folders']['apks']}/{apk}")

    versionName, versionCode, sdkMin, sdkMax = read_apktool_yml()
    globals: PatchGlobals = {
        "apk": apk,
        "app_version_name": versionName,
        "app_version_code": versionCode,
        "app_sdk_version_min": sdkMin,
        "app_sdk_version_max": sdkMax,
        "patches_enabled": [],
        "patches_statuses": [],
    }

    statuses = select_and_apply_patches(globals)
    for status in statuses:
        log.info(f"{status['name']} - {status['status']}")

    if not all(status["status"] for status in statuses):
        log.warning("Not all patches were applied, do you want to continue?")
        if not confirm("", "y", "n"):
            log.info("Cancelled")
            exit(0)

    if not args.no_compile:
        shutil.rmtree(config["folders"]["out"], ignore_errors=True)
        newApk = apk.removesuffix(".apk") + "-patched.apk"
        log.info("Compile APK")
        compile_apk(f"{config['folders']['out']}/{newApk}")
        log.info("Zipalign and Sign APK")
        sign_apk(f"{config['folders']['out']}/{newApk}")

    log.info("Finished")
    exit(0)

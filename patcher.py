from scripts.download_tools import check_and_download_all_tools
from scripts.patch_funcs import PatchGlobals, select_and_apply_patches
from scripts.repository import add_repository, fetch_repositories
from scripts.utils import (
    check_java_version,
    compile_apk,
    decompile_apk,
    list_apks,
    read_apktool_yml,
    select_apk,
)
from config import args, config, log
from time import time

if __name__ == "__main__":
    if args.repo_add:
        add_repository(args.repo_add)
        exit(0)
    if args.repo_update:
        fetch_repositories()
        exit(0)

    check_and_download_all_tools()
    check_java_version()

    apk = args.apk or select_apk(list_apks())
    log.info(f"selected apk: {apk}")

    start_time = time()
    if not args.no_decompile:
        decompile_apk(f"{config['folders']['apks']}/{apk}")
    # if not args.no_compile:
    #     compile_apk(apk)
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

    log.info(f"patching took {int(time() - start_time)} seconds")
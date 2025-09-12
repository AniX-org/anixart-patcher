from scripts.download_tools import check_and_download_all_tools
from scripts.repository import add_repository, fetch_repositories
from scripts.utils import (
    check_java_version,
    compile_apk,
    decompile_apk,
    list_apks,
    select_apk,
)
from config import args, config
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

    start_time = time()
    if not args.no_decompile:
        decompile_apk(f"{config['folders']['apks']}/{apk}")
    # if not args.no_compile:
    #     compile_apk(apk)

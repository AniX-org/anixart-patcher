from scripts.download_tools import check_and_download_all_tools
from scripts.repository import add_repository, fetch_repositories
from scripts.utils import check_java_version
from config import args

if __name__ == "__main__":
    if args.repo_add:
        add_repository(args.repo_add)
        exit(0)
    if args.repo_update:
        fetch_repositories()
        exit(0)

    check_and_download_all_tools()
    check_java_version()
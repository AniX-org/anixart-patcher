from scripts.download_tools import check_and_download_all_tools
from scripts.utils import check_java_version

if __name__ == "__main__":
    check_and_download_all_tools()
    check_java_version()
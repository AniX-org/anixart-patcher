import subprocess
from config import log, config


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

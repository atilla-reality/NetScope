import os
import platform


def detect_platform():
    if os.path.exists("/proc/ish"):
        return "ish"

    if os.environ.get("ISH"):
        return "ish"

    prefix = (os.environ.get("PREFIX") or "").lower()

    if "com.termux" in prefix:
        return "termux"

    system = platform.system().lower()

    if system == "windows":
        return "windows"

    if system == "linux":
        return "linux"

    return "unknown"

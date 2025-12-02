import os
import platform

def shutdown():
    system = platform.system().lower()
    if "windows" in system:
        os.system("shutdown /s /t 1")
    elif "linux" in system or "darwin" in system:  # darwin = macOS
        os.system("shutdown now")
    else:
        print("Unsupported OS")

def restart():
    system = platform.system().lower()
    if "windows" in system:
        os.system("shutdown /r /t 1")
    elif "linux" in system or "darwin" in system:
        os.system("reboot")
    else:
        print("Unsupported OS")


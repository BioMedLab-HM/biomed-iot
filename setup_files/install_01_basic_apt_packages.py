from .setup_utils import run_bash
import os

LOG_01 = "install_01_basic_apt_packages.log"

def install_basic_apt_packages():
    commands = [
        "apt update",
        "apt install -y python3-pip python3-venv python3-dev",
        "apt install -y curl inotify-tools zip adduser git",
        "apt install -y libopenjp2-7 libtiff6 libfontconfig1",
    ]
    for command in commands:
        run_bash(command, LOG_01)

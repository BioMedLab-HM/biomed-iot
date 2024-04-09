"""Utility functions for the setup process"""

import os
import random
import string
import subprocess


def get_linux_user():
    linux_user = os.getenv("SUDO_USER", default="")
    return linux_user

def get_setup_dir():
    setup_dir = f"/home/{get_linux_user()}/iotree42"
    return setup_dir

def get_conf_path():
    setup_dir = get_setup_dir()
    conf_path = f'{setup_dir}/setup_files/config'
    return conf_path

def get_linux_codename():
    """Extract the VERSION_CODENAME from /etc/os-release."""
    try:
        with open("/etc/os-release", "r") as file:
            for line in file:
                if line.startswith("VERSION_CODENAME"):
                    codename = line.strip().split('=')[1].replace('"', '')
                    log("Linux Codename: " + codename)
                    return codename
    except FileNotFoundError:
        msg = "The os-release file was not found."
        print(msg)
        log(msg)
        return None

# Get the directory where this script is located
  # base_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(get_setup_dir(), "setup_files", "logs")

# Ensure the logs directory exists
os.makedirs(log_dir, exist_ok=True)

def log(message, log_file_name='main.log'):
        log_file_path = os.path.join(log_dir, log_file_name)
        with open(log_file_path, 'a') as file:
            file.write(message + '\n')

def run_bash(command):
    """Execute a Bash command and return its output or an error message."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        # Return the standard output of the command
        return result.stdout 
    except subprocess.CalledProcessError as e:
        # Return the standard error output
        return f"Error executing command: {e.cmd}\nOutput:\n{e.stderr}\n"  


def get_random_string(string_length, incl_symbols=False):
    """
    Define the characters to include in the random string
    Leave incl_symbols to False (no symbols in password) for easy copy paste
    but make passwords etc. longer for security.
    """
    symbols = "!@#$%&*()_+-=[]}{|;:<>/?"
    characters = string.ascii_letters + string.digits
    if incl_symbols:
        characters += symbols
    # Generate a random string of the specified length
    rand_str = ''.join(random.choice(characters) for _ in range(string_length))
    return rand_str

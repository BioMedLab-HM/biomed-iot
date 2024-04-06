

"""
TODO: Kurzer Überblick über den Code
TODO: Kommentare im Code ergänzen/optimieren
"""

import os
import subprocess
import sys
import random
import string
import socket

# Log file path
LOG_FILE = 'installation.log'
# Open the log file globally so it can be accessed throughout the script
log = open(LOG_FILE_PATH, 'a')

def run_bash(command):
    """Executes a Bash command in the subprocess and logs its output."""
    try:
        output = subprocess.run(command, shell=True, check=True, stdout=log_file, stderr=subprocess.STDOUT, text=True)
        log.write(output))
    except subprocess.CalledProcessError as e:
        log.write(f"Error executing command: {e.cmd}\nOutput:\n{e.output}")
        sys.exit(1)


def print_logo_header():
    logo_header = """
******************************************
*  _____   _______            _  _ ___   *
* |_   _| |__   __|          | || |__ \  *
*   | |  ___ | |_ __ ___  ___| || |_ ) | *
*   | | / _ \| | '__/ _ \/ _ \__   _/ /  *
*  _| || (_) | | | |  __/  __/  | |/ /_  *
* |_____\___/|_|_|  \___|\___|  |_|____| *
*                                        *
******************************************
<<<----      SETUP OF IoTree42      --->>>
<<<----       Version v0.x.y        --->>>

For installation on a Raspberry Pi, use a PiBakery image on GitHub: 
# TODO: <insert link here>
"""
    print(logo_header)
    log.write(logo_header + '\n')


def is_supported_cpu_architecture():
    """Check system's CPU architecture."""
    cpu_architecture = platform.machine()
    if "amd64" not in cpu_architecture and "x86_64" not in cpu_architecture:
        msg = f"Your system architecture '{cpu_architecture}' is not supported. \
                Only amd64 or x86_64 is supported.\nExiting Setup"
        print(msg)
        log.write(msg)
        sys.exit(1)


def is_running_with_sudo():
    """Ensure the script is run with sudo."""
    if os.geteuid() != 0:
        msg = "This script must be run with sudo. Exiting setup"
        print(msg)
        log.write(msg)
        sys.exit(1)


def get_setup_scheme():
    """Determine the setup scheme based on user input."""
    print(f"\nTLS (Transport Layer Security) encrypts the data between your server and its users and gateways \
            (using https), ensuring the data remains private and secure. It is highly recommended for most \
            installations.\n However, if you're setting up a development environment, running tests or you're \
            in a controlled and isolated environment where encryption isn't a priority and even have limited \
            system resources (older Raspberry Pi), you might consider running without TLS (using http).\n")

    chosen_scheme = "TLS_NO_DOMAIN"  # Default scheme
    answer = input("Do you want to install IoTree42 with TLS? (Y/n, default is Y): ").strip().lower()
    if answer == 'n':
        chosen_scheme = "NO_TLS"
    else:
        # If TLS is chosen, ask about the domain
        domain_answer = input("Is the server using a domain (e.g. example.com)? (y/N, default is N): ").strip().lower()
        if domain_answer == 'y':
            chosen_scheme = "TLS_DOMAIN"
    
    log.write(chosen_scheme)
    return chosen_scheme


def confirm_proceed(question_to_ask):
    """Ask the user to confirm to proceed."""
    while True:
        user_answer = input(f"{question_to_ask} (y/n): ").strip().lower()

        if user_answer == 'y':
            break  # Exit the loop and proceed
        elif user_answer == 'n':
            msg ="You declined to proceed. Exiting setup."
            print(msg)
            log.write(msg)
            sys.exit(1)  # Exit the script with an error code
        else:
            print("Invalid response. Please enter 'Y' or 'N'.")


def random_string_of_length(string_length):
    # Define the characters to include in the random string
    characters = string.ascii_letters + string.digits  # + "_!@#$%^&*()-"
    # Generate a random string of the specified length
    rand_str = ''.join(random.choice(characters) for _ in range(string_length))
    return rand_str


def get_confirmed_text_input(input_prompt):
    """
    Example usage:
        confirmed_text = get_confirmed_text_input("Enter your password")
    """
    while True:
        print()
        input_text = input(f"{input_prompt}: ").strip()
        confirmation = input("Please repeat your entry: ").strip()

        if not input_text:
            print("Nothing entered. Please try again.")
        elif input_text == confirmation:
            return input_text
        else:
            print("First input and confirmation do not match. Please try again.")


def get_domain(setup_scheme):
    domain = ""
    if setup_scheme == "TLS_WITH_DOMAIN":
        domain = input("Enter the domain name (e.g., 'example.com') without leading 'www.': ").strip()
    return domain


def install_basic_packages():
    """Install basic packages."""
    run_bash("apt update && apt install -y package-name")

# Function definitions for other tasks...

def do_install():
    """Main installation function."""
    print_logo_header()
    is_supported_cpu_architecture()
    confirm_proceed("Do you want to proceed with the installation? This will update your system and install necessary packages.")
    is_running_with_sudo()

    hostname = socket.gethostname()
    internal_ip = socket.gethostbyname(hostname)
    domain = None
    if setup_scheme == "TLS_WITH_DOMAIN":
        domain = input("Enter the domain name (e.g., 'example.com') without leading 'www.': ").strip()
    
    # More installation steps...
    # For complex bash commands, use run_bash() function

if __name__ == "__main__":
    do_install()

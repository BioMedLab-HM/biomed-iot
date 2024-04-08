"""
TODO: Kurzer Überblick über den Code
TODO: Kommentare im Code ergänzen/optimieren
"""

import os
import subprocess
import sys
import socket
import platform
import re
from setup_files.setup_utils import get_linux_user, get_setup_dir, get_random_string, run_bash, log
from setup_files.write_config_file import write_config_file
from setup_files.install_01_basic_apt_packages import install_basic_apt_packages
from setup_files.install_02_security_packages import install_security_packages
from dev.iotree42.setup_files.install_08_postgres import install_postgres
from setup_files.install_03_docker  import install_docker
from setup_files.install_04_nodered import install_nodered


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
    log(logo_header + '\n')


def get_and_check_cpu_architecture():
    """Check system's CPU architecture."""
    supported_architectures = ["amd64", "x86_64", "arm64", "aarch64"]
    cpu_architecture = platform.machine()
    if cpu_architecture.lower() not in supported_architectures:
        msg = (f"Your system architecture '{cpu_architecture}' is not "
            "supported. Only "amd64", "x86_64", "arm64"or  "aarch64" is "
            "supported.\nExiting Setup"
        )
        print(msg)
        log(msg)
        sys.exit(1)
    
    return cpu_architecture


def is_running_with_sudo_or_exit_setup():
    """Ensure the script is run with sudo."""
    if os.geteuid() != 0:
        msg = "This script must be run with sudo. Exiting setup"
        print(msg)
        log(msg)
        sys.exit(1)


def get_setup_scheme():
    """Determine the setup scheme based on user input."""
    print(f"\nTLS (Transport Layer Security) encrypts the data between your "
        "server and its users and gateways (using https), ensuring the data "
        "remains private and secure. It is highly recommended for most "
        "installations.\nHowever, if you're setting up a development "
        "environment, running tests or you're in a controlled and isolated "
        "environment where encryption isn't a priority and even have limited "
        "system resources (older Raspberry Pi), you might consider running "
        "without TLS (using http).\n"
    )
    chosen_scheme = "NO_TLS"  # Default scheme without TLS encryption
    answer = input("Shall your IoTree42 use TLS encryption for MQTT messages? "
        "(Y/n, default is n): ").strip().lower()
    if answer == 'y':
        chosen_scheme = "TLS_NO_DOMAIN"
        # Ask about the domain
        domain_answer = input("Is the server using a domain name like "
            "'example.com')? (y/N, default is N): ").strip().lower()
        if domain_answer == 'y':
            chosen_scheme = "TLS_DOMAIN"
    
    log("Chosen setup scheme: " + chosen_scheme)
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
            log(msg)
            sys.exit(1)  # Exit the script with an error code
        else:
            print("Invalid response. Please enter 'Y' or 'N'.")


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
            print("Your inputs do not match. Please try again.")


def prompt_for_password(required_length=12):
    """
    Parameters:
    - required_length (int): The minimum required length of the password.
    Returns:
    - str: The user-provided password that meets the criteria.
    """
    password_pattern = re.compile(r"""
    (?=.*[A-Z])     # at least one uppercase letter
    (?=.*[a-z])     # at least one lowercase letter
    (?=.*\d)        # at least one digit
    (?=.*[!@#$%%&*()_+\-=\[\]{}|;:'"<>,.?/]) # at least one special character
    .{%d,}          # at least required_length characters
    """ % required_length, re.VERBOSE)

    while True:
        password = get_confirmed_text_input("Enter and remember a safe "
            f"password (min length {required_length}) for your IoTree42 admin "
            "user\nIt must contain at least one uppercase letter, one "
            "lowercase letter, one digit and one special character from "
            "!@#$%&*()_+-=[]}{|;:<>/?,"
        )
        if password_pattern.match(password):
            return password
        else:
            print("Password does not meet the criteria.\n")


def get_domain(setup_scheme):
    domain = ""
    if setup_scheme == "TLS_DOMAIN":
        domain = input("Enter the domain name (e.g., 'example.com') "
                        "without leading 'www.': ").strip()
    log("Entered Domain: " + domain)
    return domain


def get_credentials_for_pw_reset():
    question = ("\nDo you want to Enter the credentials for the website's "
        "password reset function?\nYou can add the credentials for the "
        "website's password reset function later in /etc/iotree/settings.toml")
    while True:
        user_answer = input(f"{question} (y/n): ").strip().lower()
        if user_answer == 'y':
            pwreset_email = get_confirmed_text_input("Enter the email address "
                "for the website's password reset function")
            pwreset_pass = get_confirmed_text_input("Enter the password "
                "for the website's password reset function")
            msg = "Credentials for password reset functions have been entered"
            break
        elif user_answer == 'n':
            msg = "No credentials for password reset function have been entered"
            pwreset_email = ""
            pwreset_pass = ""
            break
        else:
            print("Invalid response. Please enter 'Y' or 'N'.")
    print(msg)
    log(msg)
    return pwreset_email, pwreset_pass


def create_directories():
    # Create a temporary folder for config files within setup_dir
    tmp_dir = os.path.join(get_setup_dir(), "setup_files", "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    log("Directory 'setup_files/tmp' created. Path: " + tmp_dir)

    # Create a folder for the project-wide config.toml file
    config_dir = "/etc/iotree"
    os.makedirs(config_dir, exist_ok=True)
    log("Directory '/etc/iotree' created. Path: " + config_dir)


def main():
    """ 
    MAIN INSTALLATION FUNCTION
        Content:
        - "DO SOME PRE-CHECKS"
        - "ASK FOR USER INPUT"
        - "INSTALLATION OF SOFTWARE"
          see setup files in sub directory "setup_files" 
        - "FINAL INFORMATION OUTPUT FOR THE USER"
    """

    hostname = socket.gethostname()
    internal_ip = socket.gethostbyname(hostname)
    linux_user = get_linux_user()
    setup_dir = get_setup_dir()
    django_admin_name = None
    django_admin_pass = None
    django_admin_email = None
    pwreset_email = None
    pwreset_email_pass = None
    domain = None
    setup_scheme = None

    print_logo_header()
    
    """ DO SOME PRE-CHECKS """
    arch = get_and_check_cpu_architecture()

    is_running_with_sudo_or_exit_setup()

    print("\nTo make sure your system is up to date, run 'sudo apt update' "
        "and 'sudo apt upgrade' before setup.\n"
    )
    confirm_proceed("Do you want to proceed? Otherwise please update, upgrade "
        "and reboot - then start setup again."
    )


    """ ASK FOR USER INPUT """
    setup_scheme = get_setup_scheme()

    domain = get_domain(setup_scheme)

    django_admin_name = get_confirmed_text_input("Enter and remember a safe "
        "username for your website admin user and mosquitto-admin"
    )

    print("Enter and remember a safe password (>= 12 characters) "
        "for your IoTree42 admin user"
    )
    django_admin_pass = prompt_for_password(12)

    django_admin_email = get_confirmed_text_input("Enter email address for "
        "your website's admin user"
    )

    pwreset_email, pwreset_pass = get_credentials_for_pw_reset()
    

    """ INSTALLATION OF SOFTWARE """

    print("\nThis will install Iotree42 with server installation scheme: "
        f"{setup_scheme}"
    )
    confirm_proceed("Do you want to proceed with the installation of "
        "IoTree42, including necessary packages and services?"
    )
    msg = (f"\nStarting installation of IoTree42 for user '{linux_user}'. "
        "Please do not interrupt!\n"
    )
    print(msg)
    log(msg)
    
    # TODO: build gateway zip file

    # create_directories()
    
    # install_basic_apt_packages()
    log("Basic apt packages installed")
    
    # install_security_packages()
    log("Security Packages installed")

    # install_docker()
    log("Docker installed")

    # nodered_config_data = install_nodered(setup_scheme)
    log("Node-RED installed")

    # TODO: install_influxdb(arch)
    log("InfluxDB installed")

    # TODO: install_grafana(arch)
    log("Grafana installed")

    # TODO: install_mosquitto(setup_scheme, arch)
    log("Mosquitto Broker installed")

    # postgres_config_data = install_postgres()
    log("PostgreSQL database installed")

    # TODO: install_django()
    log("Django installed")

    # TODO: install_gunicorn()
    log("Gunicorn installed")

    # TODO: install_nginx()
    log("NGINX installed")


    """WRITE CONFIG FILE"""
    # TODO: verketten der dicts aus den Returnwerten der installationsroutinen
    values = {
        
    }

    destination = '/etc/iotree/config.toml'
    write_config_file(values, destination)


    """ FINAL INFORMATION OUTPUT FOR THE USER """
    # TBD
    # set pw reset credentials in config.toml


if __name__ == "__main__":
    main()

import os
import requests
from time import sleep
from requests.auth import HTTPBasicAuth
from .setup_utils import run_bash, log, get_random_string, get_setup_dir, get_conf_path

GRAFANA_INSTALL_LOG_FILE_NAME = 'install_06_grafana.log'


def install_grafana(architecture, setup_scheme, ip_address, domain):
    """
    Install Grafana OSS (Open Source) Version based on the provided architecture and setup scheme.
    Download pages:
        https://grafana.com/grafana/download?edition=oss&platform=linux
        https://grafana.com/grafana/download?edition=oss&platform=arm
    """
    setup_dir = get_setup_dir()
    conf_dir = get_conf_path()
    grafana_files_dir = f'{setup_dir}/setup_files/tmp/grafana_install_files'
    new_admin_username = "grafana-admin-" + get_random_string(10)
    new_admin_password = get_random_string(20)
    host = 'localhost'
    port = 3000

    installation_commands_amd64 = [
        # Ensure the temp directory exists and enter it
        f'mkdir -p {grafana_files_dir} && cd {grafana_files_dir} && '
        +
        # TODO: setup routine
        'sudo apt-get install -y adduser libfontconfig1 musl && '
        + 'wget https://dl.grafana.com/oss/release/grafana_10.4.2_amd64.deb && '
        + 'sudo dpkg -i grafana_10.4.2_amd64.deb && '
        +
        # Return to install_dir
        'cd -',
    ]

    installation_commands_arm64 = [
        # Ensure the temp directory exists and enter it
        f'mkdir -p {grafana_files_dir} && cd {grafana_files_dir} && '
        +
        # TODO: setup routine
        'sudo apt-get install -y adduser libfontconfig1 musl && '
        + 'wget https://dl.grafana.com/oss/release/grafana_10.4.2_arm64.deb && '
        + 'sudo dpkg -i grafana_10.4.2_arm64.deb && '
        +
        # Return to install_dir
        'cd -',
    ]

    if architecture in ['amd64', 'x86_64']:
        installation_commands = installation_commands_amd64
    elif architecture in ['arm64', 'aarch64']:
        installation_commands = installation_commands_arm64

    for command in installation_commands:
        output = run_bash(command)
        log(output, GRAFANA_INSTALL_LOG_FILE_NAME)

    # Configure grafana to start automatically using systemd
    commands = [
        'systemctl daemon-reload',
        'systemctl enable grafana-server',
        # Start grafana-server by executing
        'systemctl start grafana-server',
    ]

    for command in commands:
        output = run_bash(command)
        log(output, GRAFANA_INSTALL_LOG_FILE_NAME)

    # run_bash('echo sleeping for 5 seconds now to let grafana start ')
    # sleep(5)
    # with open(f'{conf_dir}/tmp.grafana.ini', 'r') as file:
    #     content = file.read()

    # grafana_ini_domain = domain if setup_scheme == "TLS_DOMAIN" else ip_address
    # content = content.replace('DOMAIN_OR_IP', grafana_ini_domain)
    # content = content.replace('ADMIN_USERNAME', new_admin_username)
    # content = content.replace('ADMIN_PASSWORD', new_admin_password)

    # with open(f'{setup_dir}/setup_files/tmp/grafana.ini', 'w') as file:
    #     file.write(content)
    try:
        with open(f'{conf_dir}/tmp.grafana.ini', 'r') as file:
            content = file.read()

        grafana_ini_domain = domain if setup_scheme == "TLS_DOMAIN" else "default_ip"
        content = content.replace('DOMAIN_OR_IP', grafana_ini_domain)
        content = content.replace('ADMIN_USERNAME', new_admin_username)
        content = content.replace('ADMIN_PASSWORD', new_admin_password)

        output_path = f'{setup_dir}/setup_files/tmp/grafana.ini'
        with open(output_path, 'w') as file:
            file.write(content)
        log(f"File successfully created at: {output_path}", GRAFANA_INSTALL_LOG_FILE_NAME)
    except Exception as e:
        log(f"Error during file handling: {e}", GRAFANA_INSTALL_LOG_FILE_NAME)
    
    run_bash('cp /etc/grafana/grafana.ini /etc/grafana/grafana.ini.backup')
    # output = run_bash('cp {setup_dir}/setup_files/tmp/grafana.ini /etc/grafana/grafana.ini')
    # log(output, GRAFANA_INSTALL_LOG_FILE_NAME)
    source_file = f'{setup_dir}/setup_files/tmp/grafana.ini'
    destination_file = '/etc/grafana/grafana.ini'

    log(f"Attempting to copy from {source_file} to {destination_file}", GRAFANA_INSTALL_LOG_FILE_NAME)
    if os.path.exists(source_file):
        command = f'cp {source_file} {destination_file}'
        output = run_bash(command)
        log(f"Copy operation result: {output}", GRAFANA_INSTALL_LOG_FILE_NAME)
    else:
        log("Source file grafana.ini does not exist.", GRAFANA_INSTALL_LOG_FILE_NAME)


    output = run_bash('systemctl restart grafana-server')
    log(output, GRAFANA_INSTALL_LOG_FILE_NAME)

    # TODO: REMOVE since not needed. Admin username and pw will be set in grafana.ini
    # change_grafana_password(host, port, admin_username, old_admin_password, new_admin_password)

    config_data = {
        'GRAFANA_HOST': host,
        'GRAFANA_PORT': port,
        'GRAFANA_ADMIN_USERNAME': new_admin_username,
        'GRAFANA_ADMIN_PASSWORD': new_admin_password,
    }
    log('Grafana installation done', GRAFANA_INSTALL_LOG_FILE_NAME)
    return config_data


def change_grafana_password(host, port, user, old_pw, new_pw):
    url = f"http://{host}:{port}/api/user/password"

    headers = {'Content-Type': 'application/json'}
    payload = {
        "oldPassword": old_pw,
        "newPassword": new_pw,
        "confirmNew": new_pw
    }

    response = requests.put(
        url,
        json=payload,
        headers=headers,
        auth=HTTPBasicAuth(user, old_pw)
    )

    if response.status_code == 200:
        log("Admin password changed successfully.", GRAFANA_INSTALL_LOG_FILE_NAME)
    else:
        log(f"Failed to change admin password. Status code: {response.status_code},",
            f"Response: {response.text}", GRAFANA_INSTALL_LOG_FILE_NAME)

import requests
from requests.auth import HTTPBasicAuth
from .setup_utils import run_bash, log, get_random_string, get_setup_dir, get_conf_path

GRAFANA_INSTALL_LOG_FILE_NAME = 'install_06_grafana.log'


def install_grafana(architecture, setup_scheme, ip_address, domain):
    """
    TODO: Implement Grafana setup
    Installation procedure for Grafana OSS (Open Source) Version
    Download pages:
        https://grafana.com/grafana/download?edition=oss&platform=linux
        https://grafana.com/grafana/download?edition=oss&platform=arm
    """
    setup_dir = get_setup_dir()
    conf_dir = get_conf_path()
    grafana_files_dir = f'{setup_dir}/setup_files/tmp/grafana_install_files'
    admin_username = 'admin'
    old_admin_password = admin_username
    new_admin_password = get_random_string(30)
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

    with open(f'{conf_dir}/tmp.grafana.ini', 'r') as file:
        content = file.read()

    domain = domain if setup_scheme == "TLS_DOMAIN" else ip_address
    content = content.replace('domain = DOMAIN_OR_IP', f'domain = {domain}')

    with open(f'{setup_dir}/setup_files/tmp/grafana.ini', 'x') as file:
        file.write(content)

    # Configure grafana to start automatically using systemd
    commands = [
        'cp /etc/grafana/grafana.ini /etc/grafana/grafana.ini.backup'
        'cp {setup_dir}/setup_files/tmp/grafana.ini /etc/grafana/'
        '/bin/systemctl daemon-reload',
        '/bin/systemctl enable grafana-server',
        # Start grafana-server by executing
        '/bin/systemctl start grafana-server',
    ]

    for command in commands:
        output = run_bash(command)
        log(output, GRAFANA_INSTALL_LOG_FILE_NAME)

    # FIXME: change_grafana_password api command is correct but rejected here. 
    # change_grafana_password(host, port, admin_username, old_admin_password, new_admin_password)

    config_data = {
        'GRAFANA_HOST': host,
        'GRAFANA_PORT': port,
        'GRAFANA_ADMIN_USERNAME': admin_username,
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

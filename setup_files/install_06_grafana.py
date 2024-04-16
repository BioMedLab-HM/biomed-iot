from .setup_utils import run_bash, log, get_setup_dir

GRAFANA_INSTALL_LOG_FILE_NAME = "install_06_grafana.log"


def install_grafana(architecture):
    """
    TODO: Implement Grafana setup
    Installation procedure for Grafana OSS (Open Source) Version
    Download pages: 
        https://grafana.com/grafana/download?edition=oss&platform=linux
        https://grafana.com/grafana/download?edition=oss&platform=arm 
    """
    setup_dir = get_setup_dir()
    grafana_files_dir = f'{setup_dir}/setup_files/tmp/grafana_install_files'

    installation_commands_amd64 = [
        # Ensure the temp directory exists and enter it
        f"mkdir -p {grafana_files_dir} && cd {grafana_files_dir} && " +
        # TODO: setup routine
        "sudo apt-get install -y adduser libfontconfig1 musl && " +
        "wget https://dl.grafana.com/oss/release/grafana_10.4.2_amd64.deb && " +
        "sudo dpkg -i grafana_10.4.2_amd64.deb && " +
        # Return to install_dir
        "cd -",
    ]

    installation_commands_arm64 = [
        # Ensure the temp directory exists and enter it
        f"mkdir -p {grafana_files_dir} && cd {grafana_files_dir} && " +
        # TODO: setup routine
        "sudo apt-get install -y adduser libfontconfig1 musl && " +
        "wget https://dl.grafana.com/oss/release/grafana_10.4.2_arm64.deb && " +
        "sudo dpkg -i grafana_10.4.2_arm64.deb && " +
        # Return to install_dir
        "cd -",
    ]

    if architecture in ["amd64", "x86_64"]:
        installation_commands = installation_commands_amd64
    elif architecture in ["arm64", "aarch64"]:
        installation_commands = installation_commands_arm64

    for command in installation_commands:
        output = run_bash(command)
        log(output, GRAFANA_INSTALL_LOG_FILE_NAME)

    # TODO: Modify and copy config data?
    

    config_data = {
        "GRAFANA_HOST": "localhost",
        "GRAFANA_PORT": 3000,
        "GRAFANA_ORG_NAME": "iotree42",
        # TODO: Weitere Daten?
    }
    log("Grafana installation done", GRAFANA_INSTALL_LOG_FILE_NAME)
    return config_data

from .setup_utils import run_bash, log, get_random_string

INFLUXDB_INSTALL_LOG_FILE_NAME = "install_05_influxdb.log"

def install_influxdb(architecture):
    """
    InfluxDB installation:
    InfluxDB for Ubuntu/Debian AMD64 
    (https://docs.influxdata.com/influxdb/v2.7/install/?t=Linux)
    or: https://docs.influxdata.com/influxdb/v2/install/?t=Linux
    test if running: sudo service influxdb status
    
    InfluxDB configuration:
    https://docs.influxdata.com/influxdb/v2/get-started/setup/?t=influx+CLI
    https://docs.influxdata.com/influxdb/v2/reference/config-options/

    The creation of buckets as well as read and write tokens for each django 
    user including django admin will be generated on user creation.   
    """
    influx_org_name = "iotree42"
    influx_username = get_random_string(20)
    influx_password = get_random_string(30)
    influx_operator_token = get_random_string(50)

    # installation_commands_amd64 = [
    #     # Ensure the temp directory exists and enter it
    #     "mkdir -p ~/influx_install_tmp && cd ~/influx_install_tmp",
    #     # Download and install InfluxDB
    #     "curl -LO https://dl.influxdata.com/influxdb/releases/influxdb2_2.7.5-1_amd64.deb",
    #     "sudo dpkg -i influxdb2_2.7.5-1_amd64.deb",
    #     "sudo service influxdb start",
    #     # Download and unpack the InfluxDB client, then move it
    #     "wget https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.7.3-linux-amd64.tar.gz",
    #     "tar xvzf influxdb2-client-2.7.3-linux-amd64.tar.gz",
    #     "sudo cp influx /usr/local/bin/",
    #     # Cleanup and return to install_dir
    #     "cd - && rm -rf ~/influx_install_tmp",
    #     # Disables sending telemetry data to InfluxData
    #     "echo 'reporting-disabled = \"true\"' | sudo tee -a /etc/influxdb/config.toml > /dev/null",
    # ]

    installation_commands_amd64 = [
        # Ensure the temp directory exists and enter it
        "mkdir -p ~/influx_install_tmp && cd ~/influx_install_tmp" +
        # Download and install InfluxDB
        "curl -LO https://dl.influxdata.com/influxdb/releases/influxdb2_2.7.5-1_amd64.deb" +
        "sudo dpkg -i influxdb2_2.7.5-1_amd64.deb" +
        "sudo service influxdb start" +
        # Download and unpack the InfluxDB client, then move it
        "wget https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.7.3-linux-amd64.tar.gz" +
        "tar xvzf influxdb2-client-2.7.3-linux-amd64.tar.gz" +
        "sudo cp influx /usr/local/bin/"  +
        # Cleanup and return to install_dir
        "cd - && rm -rf ~/influx_install_tmp" +
        # Disables sending telemetry data to InfluxData
        "echo 'reporting-disabled = \"true\"' | sudo tee -a /etc/influxdb/config.toml > /dev/null"
    ]

    # installation_commands_arm64 = [
    #     # Ensure the temp directory exists and enter it
    #     "mkdir -p ~/influx_install_tmp && cd ~/influx_install_tmp",
    #     # Download and install InfluxDB
    #     "curl -LO https://dl.influxdata.com/influxdb/releases/influxdb2_2.7.5-1_arm64.deb",
    #     "sudo dpkg -i influxdb2_2.7.5-1_arm64.deb",
    #     "sudo service influxdb start",
    #     # Download and unpack the InfluxDB client, then move it
    #     "wget https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.7.3-linux-arm64.tar.gz",
    #     "tar xvzf influxdb2-client-2.7.3-linux-arm64.tar.gz",
    #     "cp influx /usr/local/bin/",
    #     # Cleanup and return to install_dir
    #     "cd - && rm -rf ~/influx_install_tmp",
    #     # Disables sending telemetry data to InfluxData
    #     "echo 'reporting-disabled = \"true\"' | sudo tee -a /etc/influxdb/config.toml > /dev/null",
    # ]

    installation_commands_arm64 = [
        # Ensure the temp directory exists and enter it
        "mkdir -p ~/influx_install_tmp && cd ~/influx_install_tmp" +
        # Download and install InfluxDB
        "curl -LO https://dl.influxdata.com/influxdb/releases/influxdb2_2.7.5-1_arm64.deb" +
        "sudo dpkg -i influxdb2_2.7.5-1_arm64.deb" +
        "sudo service influxdb start" +
        # Download and unpack the InfluxDB client, then move it
        "wget https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.7.3-linux-arm64.tar.gz" +
        "tar xvzf influxdb2-client-2.7.3-linux-arm64.tar.gz" +
        "cp influx /usr/local/bin/" +
        # Cleanup and return to install_dir
        "cd - && rm -rf ~/influx_install_tmp" +
        # Disables sending telemetry data to InfluxData
        "echo 'reporting-disabled = \"true\"' | sudo tee -a /etc/influxdb/config.toml > /dev/null"
    ]


    if architecture in ["amd64", "x86_64"]:
        installation_commands = installation_commands_amd64
    elif architecture in ["arm64", "aarch64"]:
        installation_commands = installation_commands_arm64

    for command in installation_commands:  # loop unnecessary if 
        output = run_bash(command)
        log(output, INFLUXDB_INSTALL_LOG_FILE_NAME)

    # Setup with admin user, admin's token (=operator token) and an org 
    # (https://docs.influxdata.com/influxdb/v2/reference/cli/influx/setup/)
    setup_command = (
        f"influx setup --username {influx_username} --password '{influx_password}' "
        f"--token '{influx_operator_token}' --org {influx_org_name} --bucket {influx_username} --force"
    )

    run_bash(setup_command, show_output=False)
    msg = "Done: Setup with admin user, admin's token (=operator token) and an org"
    print(msg)
    log(msg, INFLUXDB_INSTALL_LOG_FILE_NAME)

    config_command = (
        f"influx config create --config-name \"{influx_org_name}\" "
        f"--host-url \"http://localhost:8086\" --org \"{influx_org_name}\" "
        f"--token \"{influx_operator_token}\""
    )

    run_bash(config_command, show_output=False)
    msg = "Done: influx config create command"
    print(msg)
    log(msg, INFLUXDB_INSTALL_LOG_FILE_NAME)

    # Retrieve organization ID
    influx_org_id = run_bash("influx org list | awk '/iotree42/ && NR>1 {print $1}'", show_output=False).strip()

    # Auth create commands: 
    # https://docs.influxdata.com/influxdb/cloud/reference/cli/influx/auth/create/
    # All-access token (Read and Write access to all buckets of this org)
    influx_all_access_token = run_bash(f"influx auth create --org {influx_org_name} --all-access --description '{influx_org_name}-all-access' | awk 'NR>1 {{print $3}}'", show_output=False).strip()

    config_data = {
        "INFLUX_HOST": "localhost",
        "INFLUX_PORT": 8086,
        "INFLUX_ADMIN_USERNAME": influx_username,
        "INFLUX_ADMIN_PASSWORD": influx_password,
        "INFLUX_ADMIN_BUCKET": influx_username,
        "INFLUX_ORG_NAME": influx_org_name,
        "INFLUX_ORG_ID": influx_org_id,
        "INFLUX_OPERATOR_TOKEN": influx_operator_token,
        "INFLUX_ALL_ACCESS_TOKEN": influx_all_access_token,
    }

    log("InfluxDB installation done", INFLUXDB_INSTALL_LOG_FILE_NAME)
    # Test if really necessary in case influxdb installation changes permissions
    # chmod 755 ./dj_iotree/staticfiles  # or for user directory alltogether
    return config_data

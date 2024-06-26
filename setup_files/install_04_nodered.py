from .setup_utils import run_bash, log, get_conf_path

NODERED_INSTALL_LOG_FILE_NAME = 'install_04_nodered.log'


def install_nodered(setup_scheme):
    """
    Node-RED installation
    Container instances can be started later on the website
    An NGINX-configuration directory with server blocks for real-time port
    resolution of nodered containers is set up. This means the container port
    will be looked up dynamically when nodered is started through the nodered
    page interface.

    TODO:
        - secret key authentication functionality + limited and custom node
            selection (e.g. influxDB node) in docker image
        - update_nginx_nodered_location.sh or nginx reload via inotifywait?
    """
    config_path = get_conf_path()
    script_path = '/etc/biomed-iot'
    tls_script_name = 'update_nginx_nodered_location_tls.sh'
    non_tls_script_name = 'update_nginx_nodered_location.sh'
    script_name = tls_script_name if setup_scheme in ['TLS_DOMAIN', 'TLS_NO_DOMAIN'] else non_tls_script_name

    cp_command = f'cp {config_path}/{script_name} {script_path}'

    commands = [
        'docker build -t custom-node-red .',  # Used 'docker pull nodered/node-red' before
        # Copy update script for nodered container locations in nginx to script_path
        f'{cp_command}',
        f'chmod +x /etc/biomed-iot/{script_name}',
    ]

    for command in commands:
        output = run_bash(command)
        log(output, NODERED_INSTALL_LOG_FILE_NAME)

    full_script_path = f'{script_path}/{script_name}'
    config_data = {'SERVERBLOCK_CREATE_SCRIPT_PATH': full_script_path}

    log('Nodered installation done', NODERED_INSTALL_LOG_FILE_NAME)
    return config_data

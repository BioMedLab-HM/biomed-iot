from .setup_utils import run_bash, log, get_random_string

GRAFANA_INSTALL_LOG_FILE_NAME = "install_grafana.log"

def install_grafana():
    """
    TODO: Implement Grafana setup
    """
    

    commands = [
        ''
    ]

    for command in commands:
        output = run_bash(command)
        log(output, GRAFANA_INSTALL_LOG_FILE_NAME)

    config_data = {

    }
    
    return config_data

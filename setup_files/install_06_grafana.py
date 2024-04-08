from .setup_utils import run_bash, get_random_string

GRAFANA_INSTALL_LOG_FILE_NAME = "install_grafana.log"

def install_grafana():
    """
    
    """
    

    commands = [
        ''
    ]

    for command in commands:
        run_bash(command, GRAFANA_INSTALL_LOG_FILE_NAME)

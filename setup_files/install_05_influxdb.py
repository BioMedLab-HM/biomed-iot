from .setup_utils import run_bash, get_random_string

INFLUXDB_INSTALL_LOG_FILE_NAME = "install_influxdb.log"

def install_influxdb():
    """
    
    """
    

    commands = [
        ''
    ]

    for command in commands:
        run_bash(command, INFLUXDB_INSTALL_LOG_FILE_NAME)

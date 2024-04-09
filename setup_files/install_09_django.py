from .setup_utils import run_bash, log, get_random_string

DJANGO_INSTALL_LOG_FILE_NAME = "install_django.log"

def install_django():
    """
    
    """
    

    commands = [
        ''
    ]

    for command in commands:
        run_bash(command)
    
    log("Django setup done", DJANGO_INSTALL_LOG_FILE_NAME)

    config_data = {

    }
    
    return config_data

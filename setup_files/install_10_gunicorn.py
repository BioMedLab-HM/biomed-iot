from .setup_utils import run_bash, log, get_random_string

GUNICORN_INSTALL_LOG_FILE_NAME = "install_gunicorn.log"

def install_gunicorn():
    """
    
    """
    

    commands = [
        ''
    ]

    for command in commands:
        run_bash(command)

    log("Gunicorn setup done", GUNICORN_INSTALL_LOG_FILE_NAME)

    config_data = {
        # zB. Pfad der Config files
    }
    
    return config_data
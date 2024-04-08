from .setup_utils import run_bash, get_random_string

GUNICORN_INSTALL_LOG_FILE_NAME = "install_gunicorn.log"

def install_gunicorn():
    """
    
    """
    

    commands = [
        ''
    ]

    for command in commands:
        run_bash(command, GUNICORN_INSTALL_LOG_FILE_NAME)

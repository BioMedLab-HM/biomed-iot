from .setup_utils import run_bash, get_random_string

DJANGO_INSTALL_LOG_FILE_NAME = "install_django.log"

def install_django():
    """
    
    """
    

    commands = [
        ''
    ]

    for command in commands:
        run_bash(command, DJANGO_INSTALL_LOG_FILE_NAME)

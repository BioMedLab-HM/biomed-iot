from .setup_utils import run_bash, get_random_string

NGINX_INSTALL_LOG_FILE_NAME = "install_nginx.log"

def install_nginx():
    """
    
    """
    

    commands = [
        ''
    ]

    for command in commands:
        run_bash(command, NGINX_INSTALL_LOG_FILE_NAME)

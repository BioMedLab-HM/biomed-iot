from .setup_utils import run_bash, log, get_random_string

NGINX_INSTALL_LOG_FILE_NAME = "install_nginx.log"

def install_nginx():
    """
    
    """
    

    commands = [
        ''
    ]

    for command in commands:
        run_bash(command)

    log("NGINX setupd done.", NGINX_INSTALL_LOG_FILE_NAME)

    config_data = {

    }
    
    return config_data
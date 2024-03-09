# Utility functions for Nodered
import subprocess
from django.conf import settings
from . import server_utils

def update_nodered_nginx_conf(instance):
    print("update_nodered_nginx_conf() ausgeführt")  # TODO: Später entfernen bzw durch log ersetzen
    # Logic to update Nginx configuration
    container_name = instance.container_name
    port = instance.container_port

    # Path to the server block create script
    # Could be replaced by a python script
    script_path = settings.NODERED_SETTINGS['SERVERBLOCK_CREATE_SCRIPT_PATH']

    # Call the script with sudo
    print("jetzt kommt die Ausführung des Bash scriptes")
    command = ['sudo', script_path, container_name, str(port)]
    result = subprocess.run(
        command,
        check=False,  # change to False to handle errors manually
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    server_utils.reload_nginx()
    
    if result.returncode != 0:
        print("Error:", result.stderr.decode())  # TODO: Später entfernen bzw durch log ersetzen


def del_nodered_nginx_conf(instance):
    '''
    Run this function when django user is deleted or if 
    delete container is implemented on the nodered dashboard page
    '''
    container_name = instance.container_name

    # Path to the server block create script.
    # Could be replaced by a python script
    script_path = settings.NODERED_SETTINGS['SERVERBLOCK_CREATE_SCRIPT_PATH']

    command = ['sudo', 'rm', script_path, container_name]
    result = subprocess.run(
        command,
        check=False,  # change to False to handle errors manually
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    server_utils.reload_nginx()
    
    if result.returncode != 0:
        print("Error:", result.stderr.decode())  # TODO: Später entfernen bzw durch log ersetzen

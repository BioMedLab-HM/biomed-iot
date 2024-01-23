# Utility functions 

import os
import subprocess


def reload_nginx():
    # Command to reload Nginx
    command = ['sudo', 'systemctl', 'reload', 'nginx']
    subprocess.run(command, check=True)
    print("Nginx reloaded successfully")


def update_nginx_configuration(instance):
    # Logic to update Nginx configuration
    path_segment = instance.container_name
    port = instance.container_port

    # Path to the script
    script_path = '/etc/iotree/update_nginx_nodered_location.sh'  # TODO: Pfad dynamisch aus config.json  lesen

    # Call the script with sudo
    print("jetzt kommt die Ausführung des Bash scriptes")
    result = subprocess.run(
    ['sudo', script_path, path_segment, str(port)],
    check=False,  # change to False to handle errors manually
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
    if result.returncode != 0:
        print("Error:", result.stderr.decode())  # TODO: Später entfernen bzw durch log ersetzen

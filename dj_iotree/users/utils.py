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

    # subprocess.run(['sudo', script_path, path_segment, str(port)], check=True)

    # new_block = f"""
    # location /nodered/{path_segment}/ {{
    #     proxy_pass http://localhost:{port};
    #     # add_header X-Frame-Options "SAMEORIGIN";  # instance only displayed within an iframe
    #     # add_header Content-Security-Policy "frame-ancestors 'self'";  # restricts embedding to the same origin as the page
    # }}
    # """
    # # Add a new or change an existing Nginx configuration file
    # nginx_conf_path = f'/etc/nginx/conf.d/nodered_locations/{path_segment}'

    # with open(nginx_conf_path, 'w') as file:
    #     file.write(new_block)
    
    # # Craceful reload to apply changes
    # reload_nginx()

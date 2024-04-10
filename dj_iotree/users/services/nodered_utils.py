# Utility functions for Nodered
import subprocess
from dev.iotree42.dj_iotree.dj_iotree.config_loader import config
from . import server_utils
import docker

class NoderedContainer():
    def __init__(self, nodered_data):
        self.name = nodered_data.container_name
        self.port = nodered_data.container_port
        self.access_token = nodered_data.access_token  # TODO: login with access token for security
        self.state = 'none'
        self.docker_client = docker.from_env()
        self.container = self.get_existing_container()

    def get_existing_container(self):
        """Attempt to get an existing container by name. Return None if not found."""
        try:
            return self.docker_client.containers.get(self.name)
        except docker.errors.NotFound:
            return None

    @staticmethod
    def check_container_state_by_name(container_name):  # for the endpoint
        docker_client = docker.from_env()
        state = ''
        try:
            container = docker_client.containers.get(container_name)
            container.reload()
            container_status = container.status
            try:
                container_health = container.attrs['State']['Health']['Status']
            except KeyError:
                container_health = 'N/A'
            # Determine the current state based on status and health
            if container_status == 'running' and container_health == 'starting':
                state = 'starting'
            elif container_status == 'running' and container_health == 'healthy':
                state = 'running'
            elif container_status == 'exited' and container_health == 'unhealthy':
                state = 'stopped'
            else:
                state = 'unavailable'
            return state
        except docker.errors.NotFound:
            return 'not_found'

    def create(self):
        if self.container is None:  # Only create a new container if one doesn't already exist
            try:
                self.container = self.docker_client.containers.run(
                    'nodered/node-red',
                    detach=True,
                    restart_policy={"Name": "unless-stopped"},
                    ports={'1880/tcp': None},
                    volumes={f'{self.name}-volume': {'bind': '/data', 'mode': 'rw'}},
                    name=self.name
                )
                self.determine_port()
            except (docker.errors.ContainerError, docker.errors.ImageNotFound) as e:
                # Log error
                self.container = None

    def stop(self):
        if self.container:
            self.determine_port()
            self.container.stop()

    def restart(self):
        if self.container:
            self.container.restart()
            self.determine_port()

    def determine_state(self):
        if self.container:
            self.container.reload()
            container_status = self.container.status
            try:
                container_health = self.container.attrs['State']['Health']['Status']
            except KeyError:
                container_health = 'N/A'
            # Determine the current state based on status and health
            if container_status == 'running' and container_health == 'starting':
                self.state = 'starting'
            elif container_status == 'running' and container_health == 'healthy':
                self.state = 'running'
            elif container_status == 'exited' and container_health == 'unhealthy':
                self.state = 'stopped'
            else:
                self.state = 'unavailable'
        
        return self.state
    
    def determine_port(self):
        try:
            if self.container:
                self.container.reload()
                self.port = self.container.attrs['NetworkSettings']['Ports']['1880/tcp'][0]['HostPort']
        except KeyError:
            self.port = '' 


def update_nodered_nginx_conf(instance):
    print("update_nodered_nginx_conf() ausgeführt")  # TODO: Später entfernen bzw durch log ersetzen
    # Logic to update Nginx configuration
    container_name = instance.container_name
    port = instance.container_port

    # Path to the server block create script
    # Could be replaced by a python script
    script_path = config.nodered.server_block_create_script_path

    # Call the script with sudo
    print("jetzt kommt die Ausführung des Bash scriptes")
    command = ['sudo', script_path, container_name, str(port)]
    result = subprocess.run(
        command,
        check=False,  # change to False to handle errors manually
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
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
    script_path = config.nodered.serverblock_create_script_path # NODERED_SETTINGS['SERVERBLOCK_CREATE_SCRIPT_PATH']

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

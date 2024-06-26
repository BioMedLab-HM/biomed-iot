# Utility functions for Nodered
import json
import os
import subprocess
import logging
import docker
import tempfile
from docker.types import Mount
from biomed_iot.config_loader import config
from . import server_utils


logger = logging.getLogger(__name__)


class NoderedContainer:
    def __init__(self, nodered_data):
        self.name = nodered_data.container_name
        self.port = nodered_data.container_port
        self.is_configured = nodered_data.is_configured
        self.nodered_data = nodered_data
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
                    'custom-node-red',
                    detach=True,
                    restart_policy={'Name': 'unless-stopped'},
                    ports={'1880/tcp': None},
                    volumes={f'{self.name}-volume': {'bind': '/data', 'mode': 'rw'}},
                    name=self.name,
                )
                self.determine_port()
            except (docker.errors.ContainerError, docker.errors.ImageNotFound) as e:
                print(e)  # TODO: Log Error
                self.container = None

    def stop(self):
        if self.container:
            self.determine_port()
            self.container.stop()

    def restart(self):
        if self.container:
            self.container.restart()
            self.determine_port()

    def delete_container(self):
        if self.container:
            self.determine_port()
            try:
                self.container.stop()
                self.container.remove()
                print(f'Container {self.name} has been deleted.')
            except docker.errors.NotFound:
                print(f'Container {self.name} not found.')
            except Exception as e:
                print(f'An error occurred: {e}')

    def copy_to_container(self, container, src_path, dest_path):
        # Create a tar archive of the file
        import tarfile
        from io import BytesIO
        stream = BytesIO()
        with tarfile.open(fileobj=stream, mode='w') as tar:
            tar.add(src_path, arcname=os.path.basename(dest_path))

        # Move the stream's pointer to the beginning
        stream.seek(0)
        container.put_archive(path=os.path.dirname(dest_path), data=stream)

    def configure_nodered_and_restart(self, user):
        logger.info("In configure_nodered_and_restart")
        # Install required Node-RED nodes
        self.container.exec_run("npm install node-red-dashboard", workdir='/usr/src/node-red')
        self.container.exec_run("npm install node-red-contrib-influxdb", workdir='/usr/src/node-red')
        output = self.container.exec_run("npm install node-red-dashboard", workdir='/usr/src/node-red')
        (output.output.decode())
        logger.info("In configure_nodered_and_restart ... AFTER 2x exec_run")
        # Get nodered flows from json file
        file_path = os.path.join(os.path.dirname(__file__), 'nodered_flows', 'flows.json')
        with open(file_path, 'r') as file:
            flows_json = file.read()

        user_topic_id = user.mqttmetadata.user_topic_id

        # Replace the placeholder 'topic_id' with the actual user's topic_id in the JSON string
        modified_flows_json = flows_json.replace("topic_id", user_topic_id)

        user_bucket_name = user.influxuserdata.bucket_name
        modified_flows_json = modified_flows_json.replace("user_bucket_name", user_bucket_name)

        # Determine the appropriate host address based on the configuration
        host_address = config.host.DOMAIN if config.host.TLS == "true" and config.host.DOMAIN else config.host.IP

        # Replace "server_ip_or_domain" with the determined host address
        modified_flows_json = modified_flows_json.replace("server_ip_or_domain", host_address)

        # Create a temporary file to save the modified JSON
        temp_flow_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json')
        with temp_flow_file as file:
            file.write(modified_flows_json)
        temp_flow_file_path = temp_flow_file.name

        self.copy_to_container(self.container, temp_flow_file_path, '/data/flows.json')

        # Restart Node-RED to apply the configurations
        self.container.restart()
        logger.info("In configure_nodered_and_restart ... AFTER container.restart")
		# Allow the nodered_manager to redirect to nodered_open view by setting self.nodered_data.is_configured = True
        self.nodered_data.is_configured = True
        self.nodered_data.save()
        logger.info("In configure_nodered_and_restart ... ENDE")

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
            self.port = None  # TODO: delete this comment if working, else revert: was ''


def update_nodered_nginx_conf(instance):
    print('update_nodered_nginx_conf() ausgeführt')  # TODO: Später entfernen bzw durch log ersetzen
    # Logic to update Nginx configuration
    container_name = instance.container_name
    port = instance.container_port

    # Path to the server block create script
    # Could be replaced by a python script
    script_path = config.nodered.SERVERBLOCK_CREATE_SCRIPT_PATH

    # Call the script with sudo
    command = ['sudo', script_path, container_name, str(port)]
    result = subprocess.run(
        command,
        check=False,  # change to False to handle errors manually
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode != 0:
        print('Error:', result.stderr.decode())  # TODO: Später entfernen bzw durch log ersetzen


def del_nodered_nginx_conf(instance):
    """
    Run this function when django user is deleted or if
    delete container is implemented on the nodered dashboard page
    """
    container_name = instance.container_name

    # Path to the server block create script.
    # Could be replaced by a python script
    script_path = config.nodered.SERVERBLOCK_CREATE_SCRIPT_PATH

    command = ['sudo', 'rm', script_path, container_name]
    result = subprocess.run(
        command,
        check=False,  # change to False to handle errors manually
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    server_utils.reload_nginx()

    if result.returncode != 0:
        print('Error:', result.stderr.decode())  # TODO: Später entfernen bzw durch log ersetzen

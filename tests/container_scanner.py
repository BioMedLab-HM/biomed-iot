"""
This script prints container state and health every second.

While this script is running, test bash commands like in this order:
    sudo docker run -d --restart always --name 123456 -p 1880 -v 123456-volume:/data nodered/node-red
    sudo docker stop 123456
    sudo docker start 123456
    sudo docker stop 123456
    sudo docker rm 123456
After deleting the stopped container with the 'rm'-command, stop this script and analyse its output.
"""

import docker
import time

# Set up Docker client
client = docker.from_env()

# Specify the name or ID of the container you want to monitor
container_name_or_id = "123456"

while True:
    try:
        # Get the container
        container = client.containers.get(container_name_or_id)

        print(f"Monitoring health and status of container: {container_name_or_id}")

        # Continuously check the container's health and status
        while True:
            # Reload container information to get updated data
            container.reload()

            # Extract health status
            try:
                container_health = container.attrs["State"]["Health"]["Status"]
            except KeyError:
                container_health = "N/A (No health checks configured)"

            # Get general container status
            container_status = container.status

            print(f"Container Status: {container_status} | Health: {container_health}")
            time.sleep(1)

    except docker.errors.NotFound:
        print(f"Container {container_name_or_id} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    # Wait for a bit before checking again
    time.sleep(1)

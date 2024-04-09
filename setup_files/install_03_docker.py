from .setup_utils import run_bash, log, get_linux_codename

DOCKER_INSTALL_LOG_FILE_NAME = "install_docker.log"

def install_docker():
    """
    # Docker installation (https://docs.docker.com/engine/install/debian/#install-using-the-repository)
    """
    linux_codename = get_linux_codename()

    # Preparing the Docker APT repository command
    docker_apt_repo_command = (
        f'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] '
        f'https://download.docker.com/linux/debian {linux_codename} stable" | '
        f'sudo tee /etc/apt/sources.list.d/docker.list > /dev/null'
    )

    commands = [
        # Add Docker's official GPG key:
        'sudo apt-get update',
        'sudo apt-get install ca-certificates curl gnupg',
        'sudo install -m 0755 -d /etc/apt/keyrings',
        'curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg',
        'sudo chmod a+r /etc/apt/keyrings/docker.gpg',

        # Add the repository to Apt sources:
        docker_apt_repo_command,
        'sudo apt-get update',

        # Install latest Docker version
        'sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin',
        'usermod -aG docker $USER'
    ]

    for command in commands:
        output = run_bash(command)
        log(output, DOCKER_INSTALL_LOG_FILE_NAME)

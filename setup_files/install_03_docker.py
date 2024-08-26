from .setup_utils import run_bash, log, get_linux_codename, get_linux_user, get_conf_path

DOCKER_INSTALL_LOG_FILE_NAME = 'install_03_docker.log'


def install_docker():
	"""
	# Docker installation (https://docs.docker.com/engine/install/debian/#install-using-the-repository)
	"""
	linux_codename = get_linux_codename()
	linux_user = get_linux_user()
	config_path = get_conf_path()

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
		f'usermod -aG docker {linux_user}',
		# f'cp {config_path}/deamon.json /etc/docker'  # icc=false not working kept for later tries
		# Script and Service for iptables to block inter-container communication on docker0
		f'cp {config_path}/iptables-docker-rules.sh /etc/biomed-iot',
		'chmod +x /etc/biomed-iot/iptables-docker-rules.sh',
		# '(sudo crontab -l 2>/dev/null; echo "@reboot /etc/biomed-iot/iptables-docker-rules.sh") | sudo crontab -'  did not work
		f'cp {config_path}/iptables-docker.service /etc/systemd/system/',
		'systemctl enable iptables-docker.service',
		'systemctl start iptables-docker.service'
	]

	for command in commands:
		output = run_bash(command)
		log(output, DOCKER_INSTALL_LOG_FILE_NAME)

	log('Docker installation done', DOCKER_INSTALL_LOG_FILE_NAME)

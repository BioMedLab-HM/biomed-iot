from .setup_utils import run_bash, log, get_conf_path, get_setup_dir, get_linux_user

GUNICORN_INSTALL_LOG_FILE_NAME = 'install_10_gunicorn.log'


def install_gunicorn():
	"""
	Installs and configures Gunicorn with systemd for Django applications.
	Generates and deploys Gunicorn socket and service configurations.
	"""
	setup_dir = get_setup_dir()
	conf_dir = get_conf_path()
	linux_user = get_linux_user()

	commands = [
		# Build gunicorn config files
		f'bash {conf_dir}/tmp.gunicorn.socket.sh > {setup_dir}/setup_files/tmp/gunicorn.socket',
		f'bash {conf_dir}/tmp.gunicorn.service.sh {linux_user} {setup_dir} > {setup_dir}/setup_files/tmp/gunicorn.service',
		f'cp {setup_dir}/setup_files/tmp/gunicorn.socket /etc/systemd/system/gunicorn.socket',
		f'cp {setup_dir}/setup_files/tmp/gunicorn.service /etc/systemd/system/gunicorn.service',
		'systemctl start gunicorn.socket',
		'systemctl enable gunicorn.socket',
	]

	for command in commands:
		output = run_bash(command)
		log(output, GUNICORN_INSTALL_LOG_FILE_NAME)

	log('Gunicorn setup done', GUNICORN_INSTALL_LOG_FILE_NAME)

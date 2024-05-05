# Utility functions
import subprocess


# TODO: stattdessen mit inotifywait lösen
def reload_nginx():
	# Command to reload Nginx
	command = ['sudo', 'systemctl', 'reload', 'nginx']
	subprocess.run(command, check=True)
	print('Nginx reloaded successfully')


def restart_gunicorn_service():
	# Command to restart gunicorn
	command = ['sudo', 'systemctl', 'restart', 'gunicorn.service']
	subprocess.run(command, check=True)
	print('gunicorn.service restarted successfully')

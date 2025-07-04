"""Utility functions for the setup process"""

import os
import random
import string
import subprocess
import sys
import secrets


def get_linux_user():
	linux_user = os.getenv('SUDO_USER', default='')
	return linux_user


def get_setup_dir():
	setup_dir = f'/home/{get_linux_user()}/biomed-iot'
	return setup_dir


def get_conf_path():
	setup_dir = get_setup_dir()
	conf_path = f'{setup_dir}/setup_files/config'
	return conf_path


def get_linux_codename():
	"""Extract the VERSION_CODENAME from /etc/os-release."""
	try:
		with open('/etc/os-release', 'r') as file:
			for line in file:
				if line.startswith('VERSION_CODENAME'):
					codename = line.strip().split('=')[1].replace('"', '')
					log('Linux Codename: ' + codename)
					return codename
	except FileNotFoundError:
		msg = 'The os-release file was not found.'
		print(msg)
		log(msg)
		return None

def is_running_with_sudo_or_exit_setup():
    """Ensure the script is run with sudo."""
    if os.geteuid() != 0:
        msg = '\nThis script must be run with sudo. Exiting setup\n'
        print(msg)
        sys.exit(1)

is_running_with_sudo_or_exit_setup()

# Get the directory where this script is located
# base_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(get_setup_dir(), 'setup_files', 'setup_logs')

# Ensure the setup_logs directory exists
os.makedirs(log_dir, exist_ok=True)


def log(message, log_file_name='main.log'):
	log_file_path = os.path.join(log_dir, log_file_name)
	with open(log_file_path, 'a') as file:
		file.write(message + '\n')


def run_bash(command, show_output=True):
	"""
	Execute a Bash command, optionally print its output to the terminal,
	and return its output or an error message.
	"""
	if show_output:
		process = subprocess.Popen(
			command,
			shell=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True,
		)
		stdout = ''
		while True:
			output = process.stdout.readline()
			if output == '' and process.poll() is not None:
				break
			if output:
				print(output.strip())
				stdout += output
		exit_code = process.poll()
		if exit_code == 0:
			return stdout.strip()  # strip is used to remove trailing newlines
		else:
			return f'Error executing command: {command}\nOutput:\n{stdout.strip()}\n'
	else:
		try:
			result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
			# Return the standard output of the command
			return result.stdout.strip()
		except subprocess.CalledProcessError as e:
			# Return the standard error output, which is captured in stdout due to redirect
			return f'Error executing command: {e.cmd}\nOutput:\n{e.stdout.strip()}\n'



def get_random_string(length, incl_symbols=False):
    """
    Generate a secure random string of given length.
    If incl_symbols is True, ensures >=1 lowercase, uppercase, digit, and symbol.
    """
    if length <= 0:
        return ''
    symbols = '!@#$%&*()_+-=[]}{|;:<>/?'
    pool = string.ascii_letters + string.digits + (symbols if incl_symbols else '')

    if incl_symbols:
        if length < 4:
            raise ValueError("Length must be at least 4 when including symbols.")
        # one from each category
        req = [secrets.choice(c) for c in (string.ascii_lowercase, string.ascii_uppercase, string.digits, symbols)]
        # fill rest and shuffle
        rest = [secrets.choice(pool) for _ in range(length - 4)]
        token = req + rest
        random.SystemRandom().shuffle(token)
        return ''.join(token)

    # simple secure choice
    return ''.join(secrets.choice(pool) for _ in range(length))


def set_setup_dir_rights():
	output = run_bash(f'chmod -R 700 {get_setup_dir()}')
	log(output)
	linux_user = get_linux_user()
	output = run_bash(f'chown -R {linux_user}:{linux_user} {get_setup_dir()}')
	log(output)

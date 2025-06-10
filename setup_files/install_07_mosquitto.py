from .setup_utils import run_bash, log, get_random_string, get_setup_dir, get_conf_path
from .config import start_mosquitto_service_after_docker as mosquitto_after_docker

MOSQUITTO_INSTALL_LOG_FILE_NAME = 'install_07_mosquitto.log'


def install_mosquitto(setup_scheme):
	setup_dir = get_setup_dir()
	config_path = get_conf_path()

	# Generate random credentials
	dynsec_admin_name = 'admin-' + get_random_string(10)
	dynsec_admin_pass = get_random_string(50)
	# dynsec_control_user = get_random_string(10)  # use admin user instead
	# dynsec_control_pw = get_random_string(50)
	mqtt_in_to_db_user = 'mqtt_in-' + get_random_string(10)
	mqtt_in_to_db_pw = get_random_string(50)
	mqtt_out_to_db_user = 'mqtt_out-' + get_random_string(10)
	mqtt_out_to_db_pw = get_random_string(50)

	# Install mosquitto broker
	output = run_bash('apt install -y mosquitto mosquitto-clients')
	log(output, MOSQUITTO_INSTALL_LOG_FILE_NAME)

	# Configure Mosquitto from template config file
	dynsec_plugin_path = run_bash("whereis mosquitto_dynamic_security.so | awk '{print $2}'")

	conf_script = 'tmp.mosquitto-biomed.conf.sh'
	file_name = 'mosquitto-biomed.conf'

	conf_command = f'bash {config_path}/{conf_script} {dynsec_plugin_path} > {setup_dir}/setup_files/tmp/{file_name}'
	output = run_bash(conf_command)
	log(output, MOSQUITTO_INSTALL_LOG_FILE_NAME)

	out = run_bash(f'cp {setup_dir}/setup_files/tmp/{file_name} /etc/mosquitto/conf.d')
	log(out, MOSQUITTO_INSTALL_LOG_FILE_NAME)

	# Initialize the Mosquitto Dynmic Security Plugin file
	init_dynsec_commands = [
		# Initialize and build dynamic-security.json file
		(f'mosquitto_ctrl dynsec init /var/lib/mosquitto/dynamic-security.json {dynsec_admin_name} {dynsec_admin_pass}'),  # noqa: E501
		# Set file permissions:
		'chown mosquitto:mosquitto /var/lib/mosquitto/dynamic-security.json',
		'chmod 700 /var/lib/mosquitto/dynamic-security.json',
	]
	for command in init_dynsec_commands:
		output = run_bash(command)
		log_text = ("Dynamic Security Plugin admin client created - "
			 "See https://mosquitto.org/documentation/dynamic-security/ for list of all commands.")
		log(log_text, MOSQUITTO_INSTALL_LOG_FILE_NAME)

	# Add Clients and Roles to dynamic-security.json using a prepared script
	dynsec_create_command_script = f'{config_path}/tmp.mosquitto-dynsec-commands.sh'
	dynsec_create_commands = (
		f'bash {dynsec_create_command_script} '
		f'{mqtt_in_to_db_user} {mqtt_in_to_db_pw} '
		f'{mqtt_out_to_db_user} {mqtt_out_to_db_pw}'
	)
	# f"{dynsec_control_user} {dynsec_control_pw} " # removed

	run_bash(dynsec_create_commands, show_output=False)
	print('dynsec_commands sent')
	log('dynsec_commands sent', MOSQUITTO_INSTALL_LOG_FILE_NAME)

	# Restart Mosquitto to apply configurations
	output = run_bash('systemctl restart mosquitto.service')
	log(output, MOSQUITTO_INSTALL_LOG_FILE_NAME)

	# Bugfix: start mosquitto service after docker service because mosquitto listens to docker network
	try:
		mosquitto_after_docker.modify_service_file()
		mosquitto_after_docker.reload_systemd()
	except Exception as e:
		print(f"An error occurred: {e}")

	# Create dict config data
	config_data = {
		'MOSQUITTO_HOST': 'localhost',
		'MOSQUITTO_PORT_EXTERNAL': 1883,
		'MOSQUITTO_PORT_INTERNAL': 1884,
		'MOSQUITTO_PORT_DOCKER': 1885,
		'DYNSEC_TOPIC': '$CONTROL/dynamic-security/v1',
		'DYNSEC_RESPONSE_TOPIC': '$CONTROL/dynamic-security/v1/response',
		'DYNSEC_ADMIN_USER': dynsec_admin_name,
		'DYNSEC_ADMIN_PW': dynsec_admin_pass,
		# "DYNSEC_CONTROL_USER": dynsec_control_user,
		# "DYNSEC_CONTROL_PW": dynsec_control_pw,
		'MQTT_IN_TO_DB_USER': mqtt_in_to_db_user,
		'MQTT_IN_TO_DB_PW': mqtt_in_to_db_pw,
		'MQTT_OUT_TO_DB_USER': mqtt_out_to_db_user,
		'MQTT_OUT_TO_DB_PW': mqtt_out_to_db_pw,
		'INOUT_TOPIC_ENABLED': 'false',  # Can be set to 'true' in /etc/biomed-iot/config.toml if you want to use the inout topic
	}

	log('Mosquitto installation done', MOSQUITTO_INSTALL_LOG_FILE_NAME)
	return config_data

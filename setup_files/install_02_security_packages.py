from .setup_utils import run_bash, log, get_conf_path

SECURITY_INSTALL_LOG_FILE_NAME = 'install_02_security_packages.log'

def install_security_packages(setup_scheme):
    config_path = get_conf_path()

    # Determine MQTT port based on TLS scheme
    mqtt_port = 1883 if setup_scheme == 'NO_TLS' else 8883

    # 1) Install and enable UFW
    ufw_install_cmds = [
        'apt install -y ufw',
        'echo',
        "echo 'To enable ufw firewall, automatic response to confirmation will be provided.'",
    ]

    # 2) Open standard ports
    ufw_port_cmds = [
        'ufw default deny incoming',
        'ufw default allow outgoing',
        'ufw allow ssh',
        'ufw allow 80/tcp',          # HTTP always allowed
    ]
    if setup_scheme != 'NO_TLS':
        ufw_port_cmds.append('ufw allow 443/tcp')  # HTTPS only if TLS

    ufw_port_cmds.append(f'ufw allow {mqtt_port}/tcp')  # MQTT on correct port
    ufw_port_cmds.append('ufw allow in from 172.17.0.0/16 to any port 8086')  # InfluxDB in Docker
    ufw_port_cmds.append('ufw allow in from 172.17.0.0/16 to any port 1885')  # Mosquitto in Docker
    ufw_port_cmds.append("echo 'y' | ufw enable")

    # 3) Append custom after.rules and reload
    ufw_after_rules_cmds = [
        'cp /etc/ufw/after.rules /etc/ufw/after.rules.bak',
        f'cat {config_path}/ufw-after-rules.txt >> /etc/ufw/after.rules',
        'ufw reload',
    ]

    # 4) Install & configure fail2ban
    fail2ban_cmds = [
        'apt install -y python3-systemd',  # for systemd logging
        'apt install -y fail2ban',
        'systemctl start fail2ban',
        'systemctl enable fail2ban',
        f'cp {config_path}/jail_custom.local /etc/fail2ban/jail.d/jail_custom.local',
        'systemctl restart fail2ban',
    ]

    # Helper to run a block of commands
    def run_block(cmd_list, block_name):
        log(f"--- Starting: {block_name} ---", SECURITY_INSTALL_LOG_FILE_NAME)
        for cmd in cmd_list:
            output = run_bash(cmd)
            log(output, SECURITY_INSTALL_LOG_FILE_NAME)
        log(f"--- Finished: {block_name} ---\n", SECURITY_INSTALL_LOG_FILE_NAME)

    # Execute each section
    run_block(ufw_install_cmds,      "UFW Install & Status")
    run_block(ufw_port_cmds,         "UFW Port Rules")
    run_block(ufw_after_rules_cmds,  "UFW Custom After-Rules")
    run_block(fail2ban_cmds,         "fail2ban Installation & Config")

    log('Security packages installed', SECURITY_INSTALL_LOG_FILE_NAME)

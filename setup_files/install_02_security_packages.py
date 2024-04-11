from .setup_utils import run_bash, log, get_setup_dir

SECURITY_INSTALL_LOG_FILE_NAME = "install_02_security_packages.log"

def install_security_packages():
    commands = [
        # Install ufw
        "apt install -y ufw",

        # Configure ufw
        "ufw allow ssh",
        "ufw allow 80",  # for http
        "ufw allow 443/tcp",  # for https
        "ufw allow 1883/tcp",  # For MQTT
        "echo",
        "echo 'To enable ufw firewall, automatic response to confirmation will be provided.'",
        "echo 'y' | sudo ufw enable",  # This sends "y" as input to the ufw enable command
        "sudo ufw status",

        # Install fail2ban
        "apt install -y fail2ban",
        "systemctl start fail2ban",
        "systemctl enable fail2ban",

        # Configure fail2ban
        f"bash config/tmp.jail.local.sh > {get_setup_dir()}/tmp/jail.local",
        f"cp {get_setup_dir()}/tmp/jail.local /etc/fail2ban/jail.local",

        # Restart fail2ban to apply any changes
        "systemctl restart fail2ban"
    ]
    for command in commands:
        output = run_bash(command)
        log(output, SECURITY_INSTALL_LOG_FILE_NAME)
        
    log ("Security packages installed", SECURITY_INSTALL_LOG_FILE_NAME)
    
from .setup_utils import run_bash, log, get_setup_dir, get_conf_path

NGINX_INSTALL_LOG_FILE_NAME = "install_11_nginx.log"

def install_nginx(setup_scheme, domain, server_ip, hostname):
    """
    Install and configure Nginx based on the selected setup scheme.
    """
    setup_dir = get_setup_dir()
    config_path = get_conf_path()

    # Install Nginx and Nginx stream module
    nginx_install_output = run_bash("apt install -y nginx libnginx-mod-stream")
    log(nginx_install_output, NGINX_INSTALL_LOG_FILE_NAME)

    commands = []

    if setup_scheme == "TLS_WITH_DOMAIN":
        # Configurations for TLS with domain
        commands = [
            "apt install -y openssl certbot python3-certbot-nginx",
            f"cp {config_path}/tmp.tls-params.conf /etc/nginx/snippets/ssl-params.conf",
            f"bash {config_path}/tmp.nginx-iotree-tls-domain.sh {setup_dir} {domain} > {setup_dir}/setup_files/tmp/nginx-iotree-tls-domain.conf",
            f"cp {setup_dir}/setup_files/tmp/nginx-iotree-tls-domain.conf /etc/nginx/sites-available/{domain}",
            f"ln -s /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled",
            "openssl dhparam -out /etc/nginx/dhparam.pem 2048",
            f"certbot --nginx --rsa-key-size 2048 -d {domain} -d www.{domain}",
            f"bash {config_path}/tmp.nginx-stream-tls_domain.conf.sh {domain} > {setup_dir}/setup_files/tmp/tmp.nginx-stream-tls_domain.conf",
            f"cp {setup_dir}/setup_files/tmp/tmp.nginx-stream-tls_domain.conf /etc/nginx/conf.d/stream.conf",
        ]

    elif setup_scheme == "TLS_NO_DOMAIN":
        # Configurations for TLS without domain (self-signed certificate)
        # TODO: Abfrage bei openssl req erscheint nicht
        commands = [
            "apt install -y openssl",
            f"cp {setup_dir}/setup_files/tmp/tmp.tls-params.conf /etc/nginx/snippets/ssl-params.conf",
            f"bash {setup_dir}/config/tmp.nginx-iotree-tls-local.sh {setup_dir} {server_ip} {hostname} > {setup_dir}/setup_files/tmp/nginx-iotree-tls-local.conf",
            f"cp {setup_dir}/setup_files/tmp/nginx-iotree-tls-local.conf /etc/nginx/sites-available/",
            "ln -s /etc/nginx/sites-available/nginx-iotree-tls-local /etc/nginx/sites-enabled",
            "openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-iotree.key -out /etc/ssl/certs/nginx-iotree.crt",
            "openssl dhparam -out /etc/nginx/dhparam.pem 2048",
            f"cp {setup_dir}/setup_files/tmp/tmp.self-signed.conf /etc/nginx/snippets/self-signed.conf",
            f"cp {setup_dir}/setup_files/tmp/tmp.tls-params.conf /etc/nginx/snippets/tls-params.conf",
            f"cp {setup_dir}/setup_files/tmp.nginx-stream-tls.conf /etc/nginx/conf.d/stream.conf",
        ]

    else:
        # Configurations for no TLS
        commands = [
            f"bash {config_path}/tmp.nginx-iotree-no-tls.sh {setup_dir} {server_ip} {hostname} > {setup_dir}/setup_files/tmp/nginx-iotree-no-tls.conf",
            f"cp {setup_dir}/setup_files/tmp/nginx-iotree-no-tls.conf /etc/nginx/sites-available/",
            "ln -s /etc/nginx/sites-available/nginx-iotree-no-tls.conf /etc/nginx/sites-enabled",
            f"cp {config_path}/tmp.nginx-stream-no-tls.conf /etc/nginx/conf.d/stream.conf",
        ]

    # Execute conditional configurations
    for command in commands:
        output = run_bash(command)
        log(output, NGINX_INSTALL_LOG_FILE_NAME)

    # Restart Nginx to implement changes
    restart_output = run_bash("systemctl restart nginx")
    log(restart_output, NGINX_INSTALL_LOG_FILE_NAME)
    
    log("Nginx setup done", NGINX_INSTALL_LOG_FILE_NAME)

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
            f"cp {config_path}/tmp.ssl-params.conf /etc/nginx/snippets/ssl-params.conf",
            f"bash {config_path}/tmp.nginx-iotree-tls-domain.sh {domain} > {setup_dir}/setup_files/tmp/nginx-iotree-tls-domain",
            f"cp {setup_dir}/setup_files/tmp/nginx-iotree-tls-domain /etc/nginx/sites-available/{domain}",
            f"ln -s /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled",
            "openssl dhparam -out /etc/nginx/dhparam.pem 2048",
            f"certbot --nginx --rsa-key-size 2048 -d {domain} -d www.{domain}",
            f"bash {config_path}/tmp.nginx-stream-tls_domain.conf.sh {domain} > {setup_dir}/setup_files/tmp/tmp.nginx-stream-tls_domain.conf",
            f"cp {setup_dir}/setup_files/tmp/tmp.nginx-stream-tls_domain.conf /etc/nginx/conf.d/nginx-stream-tls_domain.conf",
            "ln -s /etc/nginx/modules-available/nginx-stream-tls_domain.conf /etc/nginx/modules-enabled",
        ]

    elif setup_scheme == "TLS_NO_DOMAIN":
        # Configurations for TLS without domain (self-signed certificate)
        # TODO: Abfrage bei openssl req erscheint nicht
        commands = [
            "apt install -y openssl",
            f"cp {setup_dir}/setup_files/tmp/tmp.ssl-params.conf /etc/nginx/snippets/ssl-params.conf",
            f"bash {config_path}/tmp.nginx-iotree-tls-local.conf.sh {server_ip} {hostname} > {setup_dir}/setup_files/tmp/nginx-iotree-tls-local.conf",
            f"cp {setup_dir}/setup_files/tmp/nginx-iotree-tls-local.conf /etc/nginx/sites-available/",
            "ln -s /etc/nginx/sites-available/nginx-iotree-tls-local.conf /etc/nginx/sites-enabled",
            "openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-iotree.key -out /etc/ssl/certs/nginx-iotree.crt",
            "openssl dhparam -out /etc/nginx/dhparam.pem 2048",
            f"cp {setup_dir}/setup_files/tmp/tmp.self-signed.conf /etc/nginx/snippets/self-signed.conf",
            f"cp {setup_dir}/setup_files/tmp/tmp.ssl-params.conf /etc/nginx/snippets/ssl-params.conf",
            f"cp {config_path}/tmp.nginx-stream-tls.conf /etc/nginx/conf.d/nginx-stream-tls.conf",
            "ln -s /etc/nginx/modules-available/nginx-stream-tls.conf /etc/nginx/modules-enabled",
        ]

    else:
        # Configurations for no TLS
        commands = [
            f"bash {config_path}/tmp.nginx-iotree-no-tls.conf.sh {server_ip} {hostname} > {setup_dir}/setup_files/tmp/nginx-iotree-no-tls.conf",
            f"cp {setup_dir}/setup_files/tmp/nginx-iotree-no-tls.conf /etc/nginx/sites-available/",
            "ln -s /etc/nginx/sites-available/nginx-iotree-no-tls.conf /etc/nginx/sites-enabled",
            f"cp {config_path}/tmp.nginx-stream-no-tls.conf /etc/nginx/modules-available/nginx-stream-no-tls.conf",
            "ln -s /etc/nginx/modules-available/nginx-stream-no-tls.conf /etc/nginx/modules-enabled",
        ]

    # Execute conditional configurations
    for command in commands:
        output = run_bash(command)
        log(output, NGINX_INSTALL_LOG_FILE_NAME)

    output = run_bash('mkdir /etc/nginx/conf.d/nodered_locations')
    log(output, NGINX_INSTALL_LOG_FILE_NAME)

    output = run_bash("nginx -t")
    log(output, NGINX_INSTALL_LOG_FILE_NAME)

    # Restart Nginx to implement changes
    restart_output = run_bash("systemctl restart nginx")
    log(restart_output, NGINX_INSTALL_LOG_FILE_NAME)
    
    log("Nginx setup done", NGINX_INSTALL_LOG_FILE_NAME)

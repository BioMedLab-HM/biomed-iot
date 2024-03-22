#!/bin/bash
set -e  # Enable errexit (exit on error)

#
# TODO: Kurzer Überblick über den Code
# 
#
# TODO: Kommentare im Code ergänzen/optimieren

readonly FAILURE=1  # In Bash, functions return 0 (SUCCESS) by default, non-zero (FAILURE) indicates error.

print_logo_header() {
    cat <<"EOF"
******************************************
*  _____   _______            _  _ ___   *
* |_   _| |__   __|          | || |__ \  *
*   | |  ___ | |_ __ ___  ___| || |_ ) | *
*   | | / _ \| | '__/ _ \/ _ \__   _/ /  *
*  _| || (_) | | | |  __/  __/  | |/ /_  *
* |_____\___/|_|_|  \___|\___|  |_|____| *
*                                        *
******************************************
<<<----      SETUP OF IoTree42      --->>>
<<<----       Version v0.x.y        --->>>

For installation on a Raspberry Pi, use a PiBakery image on GitHub: 
# TODO: <hier Link>

EOF
}

is_supported_cpu_architecture() { 
# Checks if system's CPU architecture is 'amd64' or 'x86_64'; prints an error and returns failure if not.
    local cpu_architecture=$(uname -m)
    local cpu_arch_prefix=${cpu_architecture:0:3} 

    if [[ "$cpu_arch_prefix" != "amd" && "$cpu_arch_prefix" != "x86" ]]; then
         printf "Your system architecture, $cpu_arch_prefix, is not supported. Only amd64 or x86_64 is supported.\n"
         return $FAILURE
    fi
}

is_running_with_sudo() {
    if [[ $(whoami) != "root" ]]; then
        printf "You must run this setup with sudo rights.\n"
        printf "Usage: sudo bash setup.sh -p (public) or -l (local).\n"
        return $FAILURE
    fi
}


get_setup_scheme() {
    local chosen_scheme="TLS_NO_DOMAIN"  # Default to TLS_NO_DOMAIN

    # Inform the user about the importance of TLS
    printf "\nTLS (Transport Layer Security) encrypts the data between your server and its users and gateways (using https), ensuring the data remains private and secure. It is highly recommended for most installations.\n" >&2
    printf "However, if you're setting up a development environment, running tests or you're in a controlled and isolated environment where encryption isn't a priority and even have limited system ressources (older Raspberry Pi), you might consider running without TLS (using http).\n" >&2

    # Ask the user for their choice
    read -p "Do you want to install IoTree42 with TLS? (Y/n, default is Y): " answer

    # If the answer is a lowercase or uppercase 'n', then set the scheme to 'NO_TLS'
    case "$answer" in
        [Nn]) chosen_scheme="NO_TLS" ;;
    esac
    printf "\n" >&2
    # If TLS is chosen, ask about the domain
    if [[ "$chosen_scheme" == "TLS_NO_DOMAIN" ]]; then
        read -p "Is the server using a domain name (e.g., example.com)? (y/N, default is N): " domain_answer
        case "$domain_answer" in
            [Yy]) chosen_scheme="TLS_DOMAIN" ;;
        esac
    fi

    printf "$chosen_scheme"
}


confirm_proceed() {
    local question_to_ask=$1
    local user_answer

    while true; do
        read -p "${question_to_ask} (y/n): " user_answer

        case "$user_answer" in
            y|Y ) 
                break ;;
            n|N ) 
                printf "You declined to proceed. Exiting setup.\n" >&2
                return $FAILURE ;;
            * ) 
                printf "Invalid response. Please enter 'Y' or 'N'.\n" >&2 ;;
        esac
    done
}

get_rand_str_of_length() {
    local string_length=$1
    # LC_ALL=C (locale) ensures tr command behaves consistently
    rand_string=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c $string_length | xargs)
    printf "$rand_string"
}

get_password_min_length() {
    local required_length=$1
    local for_reason=$2
    local password
    local password_length
    local password_confirmation

    while true; do
        printf "\n" >&2
        read -s -p "Provide a secure password $for_reason (min $required_length characters): " password
        printf "\n" >&2
        password_length=${#password}
        if [[ $password_length -ge $required_length ]]; then
            read -s -p "Confirm your password: " password_confirmation
            printf "\n" >&2
            
            if [[ $password == $password_confirmation ]]; then
                printf "Your password has been accepted.\n" >&2
                break
            else
                printf "The passwords you entered do not match. Please try again.\n" >&2
            fi
        else
            printf "Your password is too short!" >&2
        fi
    done
}

get_confirmed_text_input() {
    local input_prompt=$1
    local input
    local confirmation

    while true; do
        printf "\n" >&2
        read -p "$input_prompt: " input
        read -p "Please repeat your entry: " confirmation

        if [[ -z $input ]]; then
            printf "Nothing entered. Please try again.\n" >&2
        elif [[ $input == $confirmation ]]; then
            printf "$input"
            break
        else
            printf "First input and confirmation do not match. Please try again.\n" >&2
        fi
    done
}

get_email_for_django_admin() {
    local email=""

    printf "\n\nProvide an IoTree42 admin email address. You can change it later in the file /etc/iotree/config.json\n" >&2

    while true; do
        email=$(get_confirmed_text_input "Enter an email address for your IoTree42 admin user")

        # Very basic email validity check. Maximum length of an email is 320 characters per RFC 3696
        if [[ ${#email} -le 320 && $email == *@* ]]; then
            echo "Valid max. email length and contains '@' character."
            break
        else
            echo "Invalid email criteria. Please enter a valid email."
        fi
    done
    printf "$email"
}

get_pwreset_email_credentials() {
    local pwreset_email="none"
    local pwreset_email_pass="none"

    printf "\nProvide an email address for the password reset function now or set it later in the file /etc/iotree/config.json\n" >&2
    while true; do
        read -p "Do you want to enter it now? (y/n): " answer

        case "$answer" in
            [Yy])
                pwreset_email=$(get_confirmed_text_input "Enter the password reset email address")
                printf "Provide the password associated with the password reset email: "
                pwreset_email_pass=$(get_password_min_length 12 "for the password reset email")
                break ;;
            [Nn])
                break ;;
            *)
                printf "Invalid input. Please enter 'Y' or 'N'." ;;
        esac
    done
    printf "%s %s" "$pwreset_email" "$pwreset_email_pass"
}

get_domain() {
    local setup_scheme=$1 
    local domain
    if [[ $setup_scheme = "TLS_WITH_DOMAIN" ]]; then
        read -p "Enter the domain name (e.g. 'example.com') without leading 'www.': " domain
    fi
    printf "$domain"
}

install_basic_packages() {
    : 
    # TODO: install apt necessary packages --> Funct.-Name ggf. anpassen ODER func Löschen
}

do_install() {
    # TODO: mögliche Struktur: "install basic packages" --> install_... --> confgure_... usw.

    local chosen_scheme
    local linux_user=$SUDO_USER
    local django_admin_name=""
    local django_admin_pass
    local django_admin_email
    local pwreset_email_and_pass
    local pwreset_email
    local pwreset_email_pass
    local server_ip="$(ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/')" # gets first active ip address
    local machine_name=$(hostname)
    local domain
    local setup_dir="/home/$linux_user/iotree42"
    local linux_codename=$(cat /etc/os-release | grep VERSION_CODENAME | cut -d'=' -f2)

    print_logo_header

# Checks if system is prepared for installation
    is_supported_cpu_architecture || exit $FAILURE

    printf "\nTo make sure your system is up to date, run 'sudo apt update' and 'sudo apt upgrade' before setup.\n"
    confirm_proceed "Do you want to proceed? Otherwise please update, upgrade and reboot and come back." || exit $FAILURE

    is_running_with_sudo || exit $FAILURE

# Get configuration data from user
    setup_scheme= $(get_setup_scheme) || exit $FAILURE
    printf "\nThis will install Iotree42 with server installation scheme: $setup_scheme.\n"
    confirm_proceed "Do you want to proceed?" || exit $FAILURE

    domain=$(get_domain setup_scheme)
    django_admin_name=$(get_confirmed_text_input "Enter a safe username for your website admin user (= django- and mosquitto-admin)")
    django_admin_pass=$(get_password_min_length 12 "for your IoTree42 admin user")
    django_admin_email=$(get_email_for_django_admin)
    pwreset_credentials=($(get_pwreset_email_credentials))
    pwreset_email=${pwreset_credentials[0]}
    pwreset_email_pass=${pwreset_credentials[1]}

# Update and install software
    printf "\nStarting installation of IoTree42 for user '$linux_user'. Please do not interrupt!\n" >&2
    confirm_proceed "Do you want to proceed?"
    
    # TODO: tmp folder + config befehle evtl in separatem block?
    mkdir $setup_dir/tmp  # create temporary folder for config files
    mkdir /etc/iotree  # folder for project wide config.json file
    # TODO: build reload3.sh file (bzw. vergleichbares) falls nötig
    # TODO: building gateway zip file

    # Update package lists
    apt update

    # TODO: Install/setup NTP deamon (für externe Geräte)

    # Install Python-related packages
    apt install -y python3-pip python3-venv python3-dev

    # Install neccessary libraries and other software
    # TODO: gpg + implementierung der Verschlüsselung der config.json
    apt install -y curl inotify-tools zip adduser git
    apt install -y libopenjp2-7 libtiff6 libfontconfig1

    # TODO: venv für mqtttodb Skript installieren (evtl an anderer Stelle)

    # Install server security packages fail2ban and ufw
    apt install -y fail2ban
    systemctl start fail2ban  # start if not yet startet automatically
    systemctl enable fail2ban  # automatically start on system boot
    apt install -y ufw
    ufw allow ssh # port 22
    ufw allow 80, 
    ufw allow 443/tcp # ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
    ufw enable  # activate ufw and automatically start on system boot
    # TODO: optional in fail2ban jail.local: 
        # [nginx-limit-req] 
        # enabled = true # falls Mosquitto nicht hinter nginx; `ngx_http_limit_req_module` benötigt, siehe jail.
    mkdir $setup_dir/config  # TODO: WHAT??? WHY???
    bash $setup_dir/config/tmp.jail.local.sh > $setup_dir/tmp/jail.local
    cp $setup_dir/tmp/jail.local /etc/fail2ban/jail.local
    systemctl restart fail2ban

    # install postgreSQL (https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-debian-11
    # and https://forum.mattermost.com/t/pq-permission-denied-for-schema-public/14273)
    apt install -y libpq-dev postgresql postgresql-contrib
    sudo -u postgres psql -c "CREATE DATABASE dj_iotree_db;"
    postgres_pass=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c 20 | xargs)
    sudo -u postgres psql -c "CREATE USER dj_iotree_user WITH PASSWORD '$postgres_pass';"
    # TODO: echo in postgres_pass.txt löschen. Ist nur für testzwecke
    echo $postgres_pass > /home/rene/dev/postgres_pass.txt  # diese Zeile entfernen
    sudo -u postgres psql -c "ALTER ROLE dj_iotree_user SET client_encoding TO 'utf8';"
    sudo -u postgres psql -c "ALTER ROLE dj_iotree_user SET default_transaction_isolation TO 'read committed';"
    sudo -u postgres psql -c "ALTER ROLE dj_iotree_user SET timezone TO 'UTC';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dj_iotree_db TO dj_iotree_user;"
    sudo -u postgres psql -c "ALTER DATABASE dj_iotree_db OWNER TO dj_iotree_user;"
    sudo -u postgres psql -c "GRANT USAGE, CREATE ON SCHEMA public TO dj_iotree_user;"

    # Django setup
    django_secret = get_rand_str_of_length 50
    runuser -u $linux_user -- python3 -m venv $setup_dir/dj_iotree/dj_venv
    source $setup_dir/dj_iotree/dj_venv/bin/activate
    pip install -r $setup_dir/dj_iotree/requirements.txt
    $setup_dir/dj_iotree/dj_venv/bin/python $setup_dir/dj_iotree/manage.py makemigrations
    $setup_dir/dj_iotree/dj_venv/bin/python $setup_dir/dj_iotree/manage.py migrate
    DJANGO_SUPERUSER_SCRIPT="from users.models import CustomUser; CustomUser.objects.create_superuser('$django_admin_name', '$django_admin_email', '$django_admin_pass')"
    echo $DJANGO_SUPERUSER_SCRIPT | runuser -u $linux_user -- $setup_dir/dj_iotree/dj_venv/bin/python $setup_dir/dj_iotree/manage.py shell
    $setup_dir/dj_iotree/dj_venv/bin/python $setup_dir/dj_iotree/manage.py collectstatic --noinput
    deactivate

# install server relevant packages
    # Build gunicorn config files
    bash $setup_dir/config/tmp.gunicorn.socket.sh > $setup_dir/tmp/gunicorn.socket
    bash $setup_dir/config/tmp.gunicorn.service.sh $linux_user $setup_dir > $setup_dir/tmp/gunicorn.service
    cp $setup_dir/tmp/gunicorn.socket /etc/systemd/system/gunicorn.socket
    cp $setup_dir/tmp/gunicorn.service /etc/systemd/system/gunicorn.service
    sudo systemctl start gunicorn.socket
    sudo systemctl enable gunicorn.socket

    # install and configure nginx according to selected setup scheme
    apt install -y nginx

    if [[ $setup_scheme == "TLS_WITH_DOMAIN" ]]; then
        # TODO: TLS-Setup mit Domain testen (use: "sudo nginx -t" to check for syntax errors)
        printf "\nInstalling packages for '$setup_scheme' scheme. Further user input may be neccessary\n" >&2
        apt install -y openssl  # some names still use ssl
        apt install -y certbot python3-certbot-nginx

        cp $setup_dir/tmp/tmp.tls-params.conf /etc/nginx/snippets/tls-params.conf # snippet to define TLS (formely SSL) settings in addition to certbot.
        bash $setup_dir/config/tmp.nginx-iotree-tls-public.sh $setup_dir $domain > $setup_dir/tmp/nginx-iotree-tls-public.conf
        cp $setup_dir/tmp/nginx-iotree-tls-public.conf /etc/nginx/sites-available/$domain  # renamed to domain name according to convention
        ln -s /etc/nginx/sites-available/$domain /etc/nginx/sites-enabled
        systemctl restart nginx

        openssl dhparam -out /etc/nginx/dhparam.pem 2048  # Generate Diffie-Hellman group parameters to enhance security. Using 4096 may take >> 30 min!
        certbot --nginx --rsa-key-size 2048 -d $domain -d www.$domain  # default: 2048 bit; higher values may cost server performance.
        # Certbot's systemd timer auto-renews certificates within 30 days of expiration twice daily.
        # Certbot adds a systemd timer that runs twice a day and automatically renews any certificate that’s within thirty days of expiration.
        systemctl restart nginx  # restart Nginx to implement changes

    elif [[ $setup_scheme != "TLS_NO_DOMAIN" ]]; then
        # https://www.digitalocean.com/community/tutorials/how-to-create-a-self-signed-ssl-certificate-for-nginx-on-debian-10 
        # TODO: TLS-Setup mit Selbstzertifikat testen (use: sudo nginx -t)
        printf "\nInstalling packages and doing configurations for '$setup_scheme' scheme. This can take some time.\n" >&2
        apt install -y openssl

        cp $setup_dir/tmp/tmp.tls-params.conf /etc/nginx/snippets/tls-params.conf # snippet to define TLS settings in addition to certbot.
        bash $setup_dir/config/tmp.nginx-iotree-tls-local.sh $setup_dir $server_ip $machine_name > $setup_dir/tmp/nginx-iotree-tls-local.conf
        cp $setup_dir/tmp/nginx-iotree-tls-local.conf /etc/nginx/sites-available/
        ln -s /etc/nginx/sites-available/nginx-iotree-tls-local /etc/nginx/sites-enabled

        # Create Self-Signed Certificate
        printf "Further user input may be neccessary. When prompted for 'Common Name' enter this machines hostname: '$machine_name'.\n" >&2
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-iotree.key -out /etc/ssl/certs/nginx-iotree.crt
        # TODO: Zertifikationserneuerung --> cronjob!? (besser als lange Zeitangabe)
        # TODO: openssl req evtl per config file automatisieren damit keine Nutzereingabe nötig ist

        # Configure Nginx HTTP Web Server to use TLS
        openssl dhparam -out /etc/nginx/dhparam.pem 2048  # Generate Diffie-Hellman group parameters to enhance security. Using 4096 may take >> 30 min!
        cp $setup_dir/tmp/tmp.self-signed.conf /etc/nginx/snippets/self-signed.conf  # Configuration snippet for TLS key and cert.
        cp $setup_dir/tmp/tmp.tls-params.conf /etc/nginx/snippets/tls-params.conf # Configuration snippet to define TLS settings
        
        systemctl restart nginx  # restart Nginx to implement changes

    else  # setup_scheme == "NO_TLS"
        bash $setup_dir/config/tmp.nginx-iotree-no-tls.sh $setup_dir $server_ip $machine_name > $setup_dir/tmp/nginx-iotree-no-tls.conf
        cp $setup_dir/tmp/nginx-iotree-no-tls.conf /etc/nginx/sites-available/
        ln -s /etc/nginx/sites-available/nginx-iotree-no-tls.conf /etc/nginx/sites-enabled
        
        systemctl restart nginx  # restart Nginx to implement changes
    fi

# Install main components of IoTree42

    # Mosquitto MQTT Broker
    apt install -y mosquitto mosquitto-clients

    # Add dynamic-security-plugin-path and dynamic-security.json file-path to mosquitto.conf
    local dynsec_plugin_path
    dynsec_plugin_path=$(sudo whereis mosquitto_dynamic_security.so | awk '{print $2}')
    echo "include_dir /etc/mosquitto/conf.d" >> /etc/mosquitto/mosquitto.conf

    # Initialize and build dynamic-security.json file
    dynsec_admin_name=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c 10 | xargs)
    dynsec_admin_pass=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c 20 | xargs)
    mosquitto_ctrl dynsec init /var/lib/mosquitto/dynamic-security.json $dynsec_admin_name $dynsec_admin_pass
    # Set file permissions, see https://stackoverflow.com/questions/71197601/prevent-systemctl-restart-mosquitto-service-from-resetting-dynamic-security
    # ALT: chown mosquitto /var/lib/mosquitto/dynamic-security.json
    chown mosquitto:mosquitto /etc/mosquitto/dynamic-security.json # works
    chmod 700 /var/lib/mosquitto/dynamic-security.json

    # Add Clients and Roles to dynamic-security.json
    dj_mqtt_controle_user=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c 10 | xargs)
    dj_mqtt_controle_pw=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c 20 | xargs)
    mqtt_in_to_db_user=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c 10 | xargs)
    mqtt_in_to_db_pw=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c 20 | xargs)
    mqtt_out_to_db_user=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c 10 | xargs)
    mqtt_out_to_db_pw=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c 20 | xargs)
    client_name_for_website_admin=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c 10 | xargs)
    client_pw_for_website_admin=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c 20 | xargs)

    dynsec_commands=$(bash $setup_dir/config/tmp.mosquitto-dynsec-commands.sh \
        $dj_mqtt_controle_user \
        $dj_mqtt_controle_pw \
        $mqtt_in_to_db_user \
        $mqtt_in_to_db_pw \
        $mqtt_out_to_db_user \
        $mqtt_out_to_db_pw \
        $client_name_for_website_admin \
        $client_pw_for_website_admin)

    mosquitto_pub -u $dynsec_admin_name -P $dynsec_admin_pass -h localhost -t '$CONTROL/dynamic-security/v1' -m "$dynsec_commands" -d
    
    # TODO: Hier, Python-Logik um mqtt Client für admin-Nutzer der Webseite in PostgresDB zu schreiben
    source $setup_dir/dj_iotree/dj_venv/bin/activate
    DJADMIN_MQTT_CLIENT_TO_DB_SCRIPT="$(bash $django_admin_name $client_name_for_website_admin $client_pw_for_website_admin $setup_dir/config/output_djadmin_mqtt_client_to_db_script.sh)"
    echo $DJADMIN_MQTT_CLIENT_TO_DB_SCRIPT | runuser -u $linux_user -- $setup_dir/dj_iotree/dj_venv/bin/python $setup_dir/dj_iotree/manage.py shell
    deactivate

    # Create config file for mosquitto to include into mosquitto.conf
    if [[ $setup_scheme == "NO_TLS" ]]; then
        bash $setup_dir/config/tmp.mosquitto-no-tls.conf.sh $dynsec_plugin_path > $setup_dir/tmp/mosquitto-no-tls.conf
        cp $setup_dir/tmp/mosquitto-no-tls.conf /etc/mosquitto/conf.d  # conf.d is a directory for custom conf files to include
    else 
        # https://www.google.com/search?client=safari&rls=en&q=mosquitto+self+certificate+tls&ie=UTF-8&oe=UTF-8
        bash $setup_dir/config/tmp.mosquitto-tls.conf.sh $dynsec_plugin_path > $setup_dir/tmp/mosquitto-tls.conf
        cp $setup_dir/tmp/mosquitto-tls.conf /etc/mosquitto/conf.d
    fi
    systemctl restart mosquitto.service

    # InfluxDB (https://docs.influxdata.com/influxdb/v2.7/install/?t=Linux)
    wget https://dl.influxdata.com/influxdb/releases/influxdb2-2.7.0-amd64.deb
    dpkg -i influxdb2-2.7.0-amd64.deb
    # TODO: InfluxDB configuration

    # Grafana (https://grafana.com/grafana/download?platform=linux&edition=oss)
    wget https://dl.grafana.com/oss/release/grafana_9.5.2_amd64.deb
    dpkg -i grafana_9.5.2_amd64.deb
    # TODO: Grafana configuration

    # TODO: Docker installation (https://docs.docker.com/engine/install/debian/#install-using-the-repository)
    # Add Docker's official GPG key:
    sudo apt-get update
    sudo apt-get install ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    # Add the repository to Apt sources:
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    $(. /etc/os-release && echo "$linux_codename") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    # Install latest Docker version
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    usermod -aG docker $USER

    # TODO: nodered installation
    docker pull nodered/node-red  # Container instances can be started later on the website
    # Nginx-configuration directory for Real-time Port Resolution of nodered containers, meaning, port 
    # will be looked up dynamically when clicking on 'nodered' in the website's menu
    mkdir /etc/nginx/conf.d/nodered_locations
    # Update script for nodered container locations in nginx server block
    local update_nginx_nodered_location_path=/etc/iotree/update_nginx_nodered_location.sh
    if [[ $setup_scheme == "TLS_NO_DOMAIN" ]]; then
        cp $setup_dir/config/tmp.update_nginx_nodered_location.sh $update_nginx_nodered_location_path
    else
        cp $setup_dir/config/tmp.update_nginx_nodered_location_tls.sh $update_nginx_nodered_location_path

    chmod +x /etc/iotree/update_nginx.sh  # TODO: dieses Skript per inotifywait statt djangoskript oder zumindest das "nginx reload"?

    # $linux_user ALL=(ALL) NOPASSWD: $update_nginx_nodered_location_path  # TODO: eher nicht notwendig, da dieses setup-script bereits mit sudo ausgeführt werden konnte?



    # TODO start/restart/status check: mosquitto, grafana-server, influxdb, ... bei Bedarf, sonst vorher bei den einzelnen Installationen
    systemctl start mosquitto
    service influxdb start
    # service influxdb status
        # Folgende Ausgabe erwartet:
        # influxdb.service - InfluxDB is an open-source, distributed, time series database
        # Loaded: loaded (/lib/systemd/system/influxdb.service; enabled; vendor preset: enable>
        # Active: active (running)

    # Build iotree config.json file
    # TODO: config.json Daten ergänzen/korrigieren + evtl als array?
    # TODO: Sollen die Nutzernamen für die Dienste bereits im Template stehen oder sollen sie
    # im Setup zufallsgeneriert werden?!
    bash $setup_dir/config/tmp.config.json.sh \
        $linux_user \
        $server_ip \
        $domain \
        $django_admin_name \
        $adminmail \
        $pwreset_email \
        $pwreset_email_pass \
        $django_secret \
        $postgres_pass \
        $dj_mqtt_controle_user \
        $dj_mqtt_controle_pw \
        $mqtt_in_to_db_user \
        $mqtt_in_to_db_pw \
        $mqtt_out_to_db_user \
        $mqtt_out_to_db_pw \
        # TODO: Weitere Werte in config.json: 
            # $update_nginx_nodered_location_path
            # ...s.o.
        > $setup_dir/tmp/config.json
        
    cp $setup_dir/tmp/config.json /etc/iotree/config.json
    
    # change file permissions
    chmod 744 /etc/iotree/config.json
    # TODO: und weitere

    ### TODO Make configurations ###  ODEr alles schon jeweils vorher bei den einzelnen Programminstallationen
    # setupt/generate user, pws, keys etc for:
    # config.json, mqttodb, grafana. influxdb, gunicorn, mosquitto, nginx-nossl/ssl, reload.sh, nodered
    # start/restart above services
    # build gateway.zip file
    # install Python requirements into venvs (mit spezifischer Version?)
    # crontabs?
    # set file permissions!


    ### TODO Final confirmation output to user ###
    # Alle printouts in eine txt- oder log-Datei ausgeben
    printf "\nAll entries above can be changed later in the file /etc/iotree/config.json\n" >&2

    if [ ! -e /run/gunicorn.sock ]; then echo "Check for Instructions: https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-debian-11";fi
    # TODO: oder Handbuchcheck für Fehler

    # Endpunkte (Dienste) mit ports
    # You can delete ... (if not auto delete)
    # (if anything went wrong, user should be able to redo install or to fully remove all files (uninstall routine)

    if [[ $setup_scheme == "TLS_WITH_DOMAIN" ]]; then
        printf "IMPORTANT: Check if the file paths to SSL-Certificate and Key in the stream{}-block in the file /etc/nginx/sites-available/$domain are correct! Otherwise outward MQTT-connections will not work" >&2 
        printf "--> The server can be reached at: https://$domain/ \n" >&2 
        printf "\n Optional: Rate your TLS with https://www.ssllabs.com/ssltest/. It should get an A or A+ rating\n" >&2
    else
        printf "--> The server can be reached at: http://$server_ip/ \n" >&2
    fi
    
    # ask user to reboot

    printf "\n\n\n ### FINISHED INSTALLATION OF IOTREE42 ### \n\n\n"

}

do_install "$@"

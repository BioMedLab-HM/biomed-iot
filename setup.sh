#!/bin/bash
set -e  # Enable errexit (exit on error)

#
# Kurzer Überblick über den Code
#
#

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
<hier Link>

EOF
}

is_supported_cpu_architecture() {
    local cpu_architecture=$(uname -m)
    local cpu_arch_prefix=${cpu_architecture:0:3} 

    if [[ "$cpu_arch_prefix" != "amd" && "$cpu_arch_prefix" != "x86" ]]; then
         printf "Your system architecture, $cpu_arch_prefix, is not supported. Please install IoTree42 on an amd64 or x86_64 system.\n"
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

parse_setup_scheme() {
    local chosen_scheme

    while getopts "pl" option 2>/dev/null; do  # 2>/dev/null discards error (stderr) messages
        case $option in
            p)  
                chosen_scheme="public" ;;
            l)  
                chosen_scheme="local" ;;
            ?)  
                printf "Invalid option! Usage: sudo bash setup.sh -p (public) or -l (local)\n" >&2
                return $FAILURE ;;
        esac
    done
    if [ -z "$chosen_scheme" ]; then
        printf "No options were used. Usage: sudo bash setup.sh -p (public) or -l (local)\n" >&2
        return $FAILURE
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
                printf "Invalid response. Please enter 'Y' or 'N'.\n" ;;
        esac
    done
}

prompt_for_password_of_length() {
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

prompt_for_confirmed_text_input() {
    local input_prompt=$1
    local confirmation_prompt=$2
    local input
    local confirmation

    while true; do
        printf "\n" >&2
        read -p "$input_prompt: " input
        read -p "$confirmation_prompt: " confirmation

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
    local email="none@none"

    printf "\n\nProvide an IoTree42 admin email address now or set it later in the file /etc/iotree/config.json\n" >&2
    while true; do
        read -p "Do you want to enter it now? (y/n): " answer

        case "$answer" in
            [Yy])
                # No regex testing for a valid email address was implemented due to susceptibility to errors.
                email=$(prompt_for_confirmed_text_input \
                    "Enter an email address for your IoTree42 user 'admin'" \
                    "Confirm your email address")
                break ;;
            [Nn])
                break ;;
            *)
                printf "\nInvalid input. Please enter 'Y' or 'N'.\n" >&2 ;;
        esac
    done
    printf "$email"
}

prompt_for_pwreset_email_credentials() {
    local pwreset_email="none"
    local pwreset_email_pass="none"

    printf "\nProvide an email address for the password reset function now or set it later in the file /etc/iotree/config.json\n" >&2
    while true; do
        read -p "Do you want to enter it now? (y/n): " answer

        case "$answer" in
            [Yy])
                pwreset_email=$(prompt_for_confirmed_text_input \
                    "Enter the password reset email address" \
                    "Confirm the password reset email address")
                printf "Provide the password associated with the password reset email: "
                # TODO: min Password length 12
                pwreset_email_pass=$(prompt_for_password_of_length 1 "for the password reset email")
                break ;;
            [Nn])
                break ;;
            *)
                printf "Invalid input. Please enter 'Y' or 'N'." ;;
        esac
    done
    printf "%s %s" "$pwreset_email" "$pwreset_email_pass"
}

get_ip_address() {
    local ip_address
    # TODO: Was ist mit öffentlicher IP-Adresse?
    # Extract the first IP address of the running network interface
    ip_address="$(ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/')"
    printf "$ip_address"
}

prompt_for_domain() {
    local setup_scheme=$1 
    local domain
    if [[ $setup_scheme = "public" ]]; then
        read -p "Enter the server domain name (e.g. example.com), if available. [Default: '$(hostname)']: " domain
    else
        domain=$(hostname)
    fi
    printf "$domain"
}

install_basic_packages() {
    : 
    # TODO: install apt necessary packages --> Funct.-Name ggf. anpassen ODER func Löschen
}

do_install() {
# TODO: mögliche Struktur: "install basic packages" --> install_... --> confgure_... usw.
    local setup_scheme
    local linux_user=$SUDO_USER
    local django_admin_pass
    local django_admin_email
    local pwreset_email_and_pass
    local pwreset_email
    local pwreset_email_pass
    local ip_address
    local domain
    local setup_dir="/home/$linux_user/iotree42"

    print_logo_header

# Checks if system is prepared for installation
    is_supported_cpu_architecture || exit $FAILURE

    printf "\nTo make sure your system is up to date, run 'sudo apt update' and 'sudo apt upgrade' before setup.\n"
    confirm_proceed "Do you want to proceed? Otherwise please update, upgrade and reboot and come back." || exit $FAILURE

    is_running_with_sudo || exit $FAILURE

    setup_scheme=$(parse_setup_scheme "$@") || exit $FAILURE
    printf "\nThis will install Iotree42 with server installation scheme: $setup_scheme.\n"
    confirm_proceed "Do you want to proceed?" || exit $FAILURE

# Get configuration data from user
    # linux_user=$(prompt_for_linux_user) || exit $FAILURE
    # TODO: django_admin_pass mit länge 12 in Production statt 1 zu Testzwecken
    django_admin_pass=$(prompt_for_password_of_length 1 "for your IoTree42 'admin' user")
    django_admin_email=$(get_email_for_django_admin)
    pwreset_email_and_pass=($(prompt_for_pwreset_email_credentials))
    pwreset_email=${pwreset_email_and_pass[0]}
    pwreset_email_pass=${pwreset_email_and_pass[1]}
    # TODO: evtl. name: server_ip
    ip_address=$(get_ip_address)
    domain=$(prompt_for_domain setup_scheme)

# Update and install software
    printf "\nStarting installation of IoTree42 for user '$linux_user'. Please do not interrupt!\n" >&2
    confirm_proceed "Do you want to proceed?"
    printf "\nInstalling $setup_scheme\n" >&2
    
    # TODO: tmp folder + config befehle evtl in separatem block?
    mkdir $setup_dir/tmp  # create temporary folder for config files
    mkdir /etc/iotree
    # TODO: build reload3.sh file (bzw. vergleichbares) falls nötig
    # TODO: building gateway zip file

    # Update package lists
    apt update

    # Install Python-related packages
    apt install -y python3-pip python3-venv python3-dev

    # Install neccessary libraries and other software
    apt install -y curl inotify-tools zip adduser git 
    apt install -y libopenjp2-7 libtiff6 libfontconfig1

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
    mkdir $setup_dir/config
    bash $setup_dir/config/tmp.jail.local.sh > $setup_dir/tmp/jail.local
    cp $setup_dir/tmp/jail.local /etc/fail2ban/jail.local
    systemctl restart fail2ban

    # install postgreSQL (https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-debian-11)
    apt install -y libpq-dev postgresql postgresql-contrib
    sudo -u postgres psql -c "CREATE DATABASE dj_iotree_db;"
    postgrespass=$(LC_ALL=C tr -dc 'A-Za-z0-9_!@#$%^&*()-' < /dev/urandom | head -c 20 | xargs) # LC_ALL=C (locale) ensures tr command behaves consistently
    sudo -u postgres psql -c "CREATE USER dj_iotree_user WITH PASSWORD '$postgrespass';"
    # TODO: echo in postgrespass.txt löschen. Ist nur für testzwecke
    echo $postgrespass > /home/rene/dev/postgrespass.txt  # diese Zeile entfernen
    sudo -u postgres psql -c "ALTER ROLE dj_iotree_user SET client_encoding TO 'utf8';"
    sudo -u postgres psql -c "ALTER ROLE dj_iotree_user SET default_transaction_isolation TO 'read committed';"
    sudo -u postgres psql -c "ALTER ROLE dj_iotree_user SET timezone TO 'UTC';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dj_iotree_db TO dj_iotree_user;"
    sudo -u postgres psql -c "ALTER DATABASE dj_iotree_db OWNER TO dj_iotree_user;"
    sudo -u postgres psql -c "GRANT USAGE, CREATE ON SCHEMA public TO dj_iotree_user;"

    # TODO: venv für mqtttodb Skript installieren (evtl an anderer Stelle)

    # Django setup
    runuser -u $linux_user -- python3 -m venv $setup_dir/dj_iotree/dj_venv
    source $setup_dir/dj_iotree/dj_venv/bin/activate
    pip install -r $setup_dir/dj_iotree/requirements.txt
    $setup_dir/dj_iotree/dj_venv/bin/python $setup_dir/dj_iotree/manage.py makemigrations
    $setup_dir/dj_iotree/dj_venv/bin/python $setup_dir/dj_iotree/manage.py migrate
    DJANGO_SUPERUSER_SCRIPT="from django.contrib.auth.models import User; User.objects.create_superuser('admin', '$django_admin_email', '$django_admin_pass')"
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

    # install and configure nginx
    apt install -y nginx

    # TODO: Diese Variable weiter oben in Funktion den Nutzer abfragen
    no_tls=0  

    if [[ $no_tls -eq 0 ]]; then
        apt install -y openssl

        if [[ $setup_scheme == "public" ]]; then  
            # TODO: evtl setup_scheme refactoring. public heißt öffentlich erreichbarer Server ggf. mit www-Adresse
            printf "'public' scheme packages (with TLS encryption) installation. Further user input may be neccessary\n" >&2

            bash $setup_dir/config/tmp.nginx-iotree-ssl-public.sh $setup_dir $domain > $setup_dir/tmp/nginx-iotree-ssl-public
            cp $setup_dir/tmp/nginx-iotree-ssl-public /etc/nginx/sites-available/nginx-iotree-ssl-public
            ln -s /etc/nginx/sites-available/nginx-iotree-ssl-public /etc/nginx/sites-enabled
            systemctl restart nginx

            apt install -y certbot python3-certbot-nginx
            openssl dhparam -out /etc/nginx/dhparam.pem 4096  # Generate Diffie-Hellman group parameters to enhance security.
            cp $setup_dir/tmp/tmp.ssl-params.conf /etc/nginx/snippets/ssl-params.conf # Configuration snippet to define SSL settings
            certbot --nginx --rsa-key-size 2048 -d $domain -d www.$domain  # default: 2048 bit; higher values may cost server performance
            # Certbot's systemd timer auto-renews certificates within 30 days of expiration twice daily.
            # Certbot adds a systemd timer that runs twice a day and automatically renews any certificate that’s within thirty days of expiration.
            # Optional: test server with https://www.ssllabs.com/ssltest/
        else
            printf "'local' scheme packages (with TLS encryption) installation. This can take some time. Further user input may be neccessary. When prompted for 'Common Name' enter this machines hostname '$domain'.\n" >&2
            bash $setup_dir/config/tmp.nginx-iotree-ssl.sh $setup_dir $ip_address $domain > $setup_dir/tmp/nginx-iotree-ssl
            cp $setup_dir/tmp/nginx-iotree-ssl /etc/nginx/sites-available/nginx-iotree-ssl
            ln -s /etc/nginx/sites-available/nginx-iotree-ssl /etc/nginx/sites-enabled
            systemctl restart nginx
            # Create Self-Signed Certificate
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-iotree.key -out /etc/ssl/certs/nginx-iotree.crt
            # TODO: was passiert nach 365 Tagen?
            # Configure Nginx HTTP Web Server to use SSL
            openssl dhparam -out /etc/nginx/dhparam.pem 4096  # Generate Diffie-Hellman group parameters to enhance security.
            cp $setup_dir/tmp/tmp.self-signed.conf /etc/nginx/snippets/self-signed.conf  # Configuration snippet for SSL key and cert.
            cp $setup_dir/tmp/tmp.ssl-params.conf /etc/nginx/snippets/ssl-params.conf # Configuration snippet to define SSL settings

            # TODO: TLS setup mit Selbstzertifikat fortsetzen: https://hostadvice.com/how-to/web-hosting/vps/how-to-configure-nginx-to-use-self-signed-ssl-tls-certificate-on-ubuntu-18-04-vps-or-dedicated-server/ 
        fi
    else
        # TODO: nginx-iotree-nossl config
    fi


# Install main components of IoTree42

    # Mosquitto MQTT Broker
    apt install -y mosquitto mosquitto-clients
    # TODO Docker falls nötig

    # InfluxDB (https://docs.influxdata.com/influxdb/v2.7/install/?t=Linux)
    wget https://dl.influxdata.com/influxdb/releases/influxdb2-2.7.0-amd64.deb
    dpkg -i influxdb2-2.7.0-amd64.deb
    # TODO: InfluxDB configuration

    # Grafana (https://grafana.com/grafana/download?platform=linux&edition=oss)
    wget https://dl.grafana.com/oss/release/grafana_9.5.2_amd64.deb
    dpkg -i grafana_9.5.2_amd64.deb
    # TODO: Grafana configuration

    # TODO nodered / flowforge installation
    # TODO: Flowforge Configuration

    # TODO start/restart/status check: mosquitto, grafana-server, influxdb, ... bei Bedarf, sonst vorher bei den einzelnen Installationen
    systemctl start mosquitto
    service influxdb start
    # service influxdb status
        # Folgende Ausgabe erwartet:
        # influxdb.service - InfluxDB is an open-source, distributed, time series database
        # Loaded: loaded (/lib/systemd/system/influxdb.service; enabled; vendor preset: enable>
        # Active: active (running)

    # Build iotree config.json file
    # TODO: config.json Daten ergänzen + evtl als array?
    bash $setup_dir/config/tmp.config.json.sh \
        $linux_user \
        $ip_address \
        $domain \
        $adminmail \
        $pwreset_email \
        $pwreset_email_pass \
        $djangokey \
        $postgrespass \
        > $setup_dir/tmp/config.json
    
    cp $setup_dir/tmp/config.json /etc/iotree/config.json
    
    # change file permissions
    chmod 744 /etc/iotree/config.json
    # und weitere

    ### TODO Make configurations ###  ODEr alles schon jeweils vorher bei den einzelnen Programminstallationen
    # Certbot: https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-debian-11
    # setupt/generate user, pws, keys etc for:
    # config.json, mqttodb, grafana. influxdb, gunicorn, mosquitto, nginx-nossl/ssl, reload.sh, nodered
    # create temporary files of config-templates
    # write into temporary files 
    # copy all temporary files to destination (/etc/...)
    # start/restart above services
    # change file permissions
    # build gateway.zip file
    # install Python requirements into venvs (mit spezifischer Version?)
    # create Django admin 
    # crontabs?
    # set file permissions!


    ### TODO Final confirmation output to user ###
    printf "\nAll entries above can be changed later in the file /etc/iotree/config.json\n" >&2

    if [ ! -e /run/gunicorn.sock ]; then echo "Check for Instructions: https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-debian-11";fi
    # TODO: oder Handbuchcheck für Fehler

    # Endpunkte (Dienste) mit ports
    # You can delete ... (if not auto delete)
    # (if anything went wrong, user should be able to redo install or to fully remove all files (uninstall routine)

    if [[ $setup_scheme == "public" ]]; then
        printf "--> The server can be reached at: https://$domain/ \n" >&2 
    else
        printf "--> The server can be reached at: http://$ip_address/ \n" >&2
    fi
    
    # ask user to reboot

}

do_install "$@"
# wrapped up in a function so that for some protection against only getting 
# half the file during "curl | sh"

printf "\n!!!!!!!!!!!!!!!!!!!!!!!!!!! END !!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n"  # nur für debugging --> Entfernen!

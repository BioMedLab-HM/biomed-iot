#!/bin/sh

# TODO: 
# - Ergänzungen bei Gunicorn?
# - location /media/ ...
# - ggf. Grafana?
# - weitere Dienste?
# - Prüfen ob include snippets NACH Ergänzungen durch certbot stattfinden

# Get passed parameter
SETUP_DIR=$1
DOMAIN=$2

# Define nginx server block template:
# Certbot updates the server blocks automatically. 
# Nevertheless, listen 443, redirect are prepared here to include custom tls-params.conf

cat << EOF
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name $DOMAIN www.$DOMAIN;
    include snippets/tls-params.conf;  # in addition to certbots parameters

    location = /favicon.ico { access_log off; log_not_found off; }

    # location to Django static files
    location /static/ {
        root $SETUP_DIR/dj_iotree/staticfiles/;
    }

    # location and proxy pass to gunicorn server (the Django server)
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }

    # location files for nodered container instances
    include /etc/nginx/conf.d/nodered_locations/*;
}

server {
    listen 80;
    listen [::]:80;

    server_name $DOMAIN www.$DOMAIN;

    return 301 https://$server_name$request_uri;  # redirect to server block with port 443 listener. TODO: change 302 to 301 after successfull testing
}

stream {
    server {
        listen 8883 ssl; # Listen for MQTT over TLS
        proxy_pass localhost:1884; # Forward to Mosquitto's listener

        # IMPORTANT: Please check if the following two lines contain  the correct file path to the actual files after installation
        # ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
        # ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

        include snippets/tls-params.conf;   # contains additional params
    }
}

EOF
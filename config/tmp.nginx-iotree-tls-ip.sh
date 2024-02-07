#!/bin/sh

# TODO: 
# - Ergänzungen bei Gunicorn?
# - location /media/ ...
# - ggf. Grafana?
# - weitere Dienste?
# TODO: change 302 to 301 after successfull testing (bei redirect)

# Get passed parameter
SETUP_DIR=$1
IP_ADDRESS=$2
MACHINE_NAME=$3

# Define nginx server block template
cat << EOF
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    include snippets/self-signed.conf; # contains ssl_certificate and ssl_certificate_key
    include snippets/ssl-params.conf;  # contains additional params
    server_name $IP_ADDRESS $MACHINE_NAME;

    location = /favicon.ico { access_log off; log_not_found off; }

    # location to Django static files
    location /static/ {
        alias $SETUP_DIR/dj_iotree/staticfiles/;
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

    server_name $IP_ADDRESS $MACHINE_NAME;

    return 302 https://$server_name$request_uri;  # redirect to server block with port 443 listener. TODO: change 302 to 301 after successfull testing
}

stream {
    server {
        listen 8883 ssl; # Listen for MQTT over TLS
        proxy_pass localhost:1884; # Forward to Mosquitto's listener

        include snippets/self-signed.conf;
        include snippets/ssl-params.conf;
    }
}
EOF
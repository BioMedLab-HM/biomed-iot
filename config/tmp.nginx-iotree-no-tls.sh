#!/bin/sh

# TODO: 
# - Ergänzungen bei Gunicorn?
# - location /media/ ...
# - ggf. Grafana?
# - weitere Dienste?

# Not using TLS encryption is not recommended but may be considered when security is less important and 
# system ressources are limited (e.g. on older Raspberry Pi)

# Get passed parameter
SETUP_DIR=$1
IP_ADDRESS=$2
MACHINE_NAME=$3

# Define nginx server block template
cat << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $IP_ADDRESS $MACHINE_NAME;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root $SETUP_DIR/dj_iotree;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }

    include /etc/nginx/conf.d/nodered_locations/*;
}
EOF
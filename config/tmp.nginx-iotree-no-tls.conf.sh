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
# Optional: Uncomment to direct MQTT traffic through nginx as reverse proxy
# stream {
#     server {
#         listen 1883;
#         proxy_pass localhost:1883;
#     }
# }
EOF
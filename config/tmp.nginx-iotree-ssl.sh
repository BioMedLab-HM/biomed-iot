#!/bin/sh

# Get passed parameter
INSTALLATIONDIR=$1
IP_ADDRESS=$2
DOMAIN=$3

# Define nginx server block template
cat << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $IP_ADDRESS $DOMAIN;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root $INSTALLATIONDIR/dj_iotree;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
EOF
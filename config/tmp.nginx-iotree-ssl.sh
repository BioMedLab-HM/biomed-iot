#!/bin/sh

# Get passed parameter
INSTALLATIONDIR=$1
DOMAIN=$2

# Define gunicorn.socket template
cat << EOF
server {
    listen 80;
    server_name $DOMAIN;

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
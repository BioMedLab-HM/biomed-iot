#!/bin/sh

# Get passed parameter
SETUP_DIR=$1
IP_ADDRESS=$2
MACHINE_NAME=$3

# Define nginx server block template
cat << EOF
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    include snippets/self-signed.conf;
    include snippets/ssl-params.conf;
    server_name $IP_ADDRESS $MACHINE_NAME;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root $SETUP_DIR/dj_iotree;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}

server {
    listen 80;
    listen [::]:80;

    server_name $IP_ADDRESS $DOMAIN;

    return 302 https://$server_name$request_uri;  # change 302 to 301 after successfull testing
}
EOF
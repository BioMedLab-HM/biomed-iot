#!/bin/sh

# Not using TLS encryption is not recommended but may be considered when security is less important and 
# system ressources are limited (e.g. on older Raspberry Pi)

# Get passed parameter
IP_ADDRESS=$1
MACHINE_NAME=$2

# Define nginx server block template
cat << EOF
server {
    listen 80;
    listen [::]:80;
        server_name $IP_ADDRESS $MACHINE_NAME;

    location = /favicon.ico { access_log off; log_not_found off; }

    # location to Django static files
    location /static/ {
        alias /var/www/biomed-iot/static/;
    }

    location /media/ {
        root /var/www/biomed-iot/media/;
    }

    location = /robots.txt {
        alias /var/www/biomed-iot/static/robots.txt;
    }

    # location and proxy pass to gunicorn server (the Django server)
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }

    location /ui {
        return 301 \$scheme://\$host/nodered-dashboard;
    }

    # location files for nodered container instances
    include /etc/nginx/conf.d/nodered_locations/*.conf;
}
EOF

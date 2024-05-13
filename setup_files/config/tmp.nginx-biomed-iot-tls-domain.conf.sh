#!/bin/sh

# TODO: 
# - Ergänzungen bei Gunicorn?
# - location /media/ ...
# - ggf. Grafana?
# - weitere Dienste?
# - Prüfen ob include snippets NACH Ergänzungen durch certbot stattfinden

# Get passed parameter
DOMAIN=$1

# Define nginx server block template:
# Certbot updates the server blocks automatically. 
# Nevertheless, listen 443, redirect are prepared here to include custom tls-params.conf

cat << EOF
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name $DOMAIN www.$DOMAIN;
    include snippets/ssl-params.conf;  # in addition to certbots parameters

    location = /favicon.ico { access_log off; log_not_found off; }

    # location to Django static files
    location /static/ {
        alias /var/www/biomed-iot/static/;
    }

    # location and proxy pass to gunicorn server (the Django server)
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }

    location /ui {
        return 301 $scheme://$host/nodered-dashboard;
    }

    # location files for nodered container instances
    include /etc/nginx/conf.d/nodered_locations/*.conf;
}

server {
    listen 80;
    listen [::]:80;

    server_name $DOMAIN www.$DOMAIN;

    return 302 https://$server_name$request_uri;  # redirect to server block with port 443 listener. TODO: change 302 to 301 after successfull testing
}
EOF

#!/bin/sh

# TODO: 
# - Ergänzungen bei Gunicorn?
# - location /media/ ...
# - ggf. Grafana?
# - weitere Dienste?
# TODO: change 302 to 301 after successfull testing (bei redirect)

# Get passed parameter
IP_ADDRESS=$1
MACHINE_NAME=$2

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
        alias /var/www/biomed-iot/static/;
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

server {
    listen 80;
    listen [::]:80;

    server_name $IP_ADDRESS $MACHINE_NAME;

    return 301 https://\$server_name\$request_uri;  # redirect to server block with port 443 listener. Changed 302 to 301 after successfull testing
}
EOF

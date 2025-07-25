#!/bin/sh

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
    server_tokens off;

    # ssl_certificate     /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # “Managed by Certbot” defaults (TLS settings, DH params, stapling…)
    # include /etc/letsencrypt/options-ssl-nginx.conf;

    # Custom headers (HSTS, X‑Frame‑Options, etc.)
    include snippets/nginx_security_options.conf;

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

server {
    listen 80;
    listen [::]:80;

    server_name $DOMAIN www.$DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;  # webroot for Certbot
    }

    return 301 https://\$host\$request_uri;  # redirect to server block with port 443 listener. Changed 302 to 301 after successfull testing
}
EOF

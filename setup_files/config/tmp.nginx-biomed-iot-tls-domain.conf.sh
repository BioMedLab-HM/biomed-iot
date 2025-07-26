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

    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;

    # From https://github.com/certbot/certbot/blob/d8acf7cea0cd3216f38480803a1cc12b6970305b/certbot-nginx/src/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf#L4
    # Contents are based on https://ssl-config.mozilla.org
    ssl_session_cache shared:le_nginx_SSL:10m;
    ssl_session_timeout 1440m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384";

    # Custom headers (X‑Frame‑Options, etc.)
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

    # Serve ACME challenges over HTTP (don't redirect these)
    location ^~ /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect everything else to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

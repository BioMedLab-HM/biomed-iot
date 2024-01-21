#!/bin/sh

# Define update script for updating nodered container location in nginx server block
# https://hobbytronics.pk/node-red-nginx-reverse-proxy/

# Parameters: $1 - Path Segment, $2 - Port

PATH_SEGMENT=$1
PORT=$2
NGINX_CONF_PATH="/etc/nginx/conf.d/nodered_locations/$PATH_SEGMENT.conf"

mkdir -p /etc/nginx/conf.d/nodered_locations/

# Create or overwrite the Nginx configuration for the given path segment
cat > $NGINX_CONF_PATH <<EOF
location /nodered/$PATH_SEGMENT/ {
    proxy_set_header X-Frame-Options "";
    proxy_hide_header X-Frame-Options;
    proxy_http_version 1.1;
    rewrite ^/nodered/$PATH_SEGMENT/(.*)$ /\$1 break;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_pass http://localhost:$PORT;
    add_header X-Frame-Options "SAMEORIGIN";  # instance only displayed within an iframe
    add_header Content-Security-Policy "frame-ancestors 'self'";  # restricts embedding to the same origin as the page
}

location ~* ^/admin/(.+\.(css|js)) {
    rewrite ^/static/contents/\$1 break;
    proxy_pass http://localhost:$PORT;
  }
EOF

# Reload Nginx
sudo nginx -s reload
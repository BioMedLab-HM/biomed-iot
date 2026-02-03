#!/bin/sh

# Define update script for updating nodered container location in nginx server block
# https://hobbytronics.pk/node-red-nginx-reverse-proxy/

CONTAINER_NAME=$1
PORT=$2
NGINX_CONF_PATH="/etc/nginx/conf.d/nodered_locations/$CONTAINER_NAME.conf"

# trim whitespace (POSIX)
PORT=$(printf '%s' "$PORT" | tr -d '[:space:]')

# port number fix:
case "$PORT" in
  ""|None|none) exit 0 ;;
  *[!0-9]*)     exit 0 ;;
esac

# numeric range check
if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
  exit 0
fi

mkdir -p /etc/nginx/conf.d/nodered_locations/

# Create or overwrite the Nginx configuration for the given path segment
cat > $NGINX_CONF_PATH <<EOF
# Proxy pass to Node-RED in the /nodered page's iframe
location /nodered/$CONTAINER_NAME/ {
    proxy_set_header X-Frame-Options "";
    proxy_hide_header X-Frame-Options;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_pass http://localhost:$PORT/;
    proxy_set_header X-Forwarded-Proto \$scheme;  # for TLS
    add_header X-Frame-Options "SAMEORIGIN";
    add_header Content-Security-Policy "frame-ancestors 'self'";
}

# Proxy pass to Node-RED dashboard in the /nodered-dashboard page's iframe
location /nodered-dashboard/$CONTAINER_NAME/ {
    proxy_set_header X-Frame-Options "";
    proxy_hide_header X-Frame-Options;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_pass http://localhost:$PORT/ui/;
    proxy_set_header X-Forwarded-Proto \$scheme;  # for TLS
    add_header X-Frame-Options "SAMEORIGIN";
    add_header Content-Security-Policy "frame-ancestors 'self'";
}
EOF

# Reload Nginx to apply changes
sudo nginx -s reload

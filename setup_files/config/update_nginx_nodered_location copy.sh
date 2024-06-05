#!/bin/sh

# Define update script for updating nodered container location in nginx server block
# https://hobbytronics.pk/node-red-nginx-reverse-proxy/

CONTAINER_NAME=$1
PORT=$2
NGINX_CONF_PATH="/etc/nginx/conf.d/nodered_locations/$CONTAINER_NAME.conf"

# Create the directory if it doesn't exist
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

    # Pass the access token to Node-RED
    # set \$access_token "";
    # if (\$arg_access_token) {
    #     set \$access_token \$arg_access_token;
    # }
    # proxy_set_header Authorization "Bearer \$access_token";
    # proxy_pass http://localhost:$PORT/;
    # Pass the access token to Node-RED as a URL parameter
    set \$access_token "";
    if (\$arg_access_token) {
        set \$access_token \$arg_access_token;
    }
    
    proxy_pass http://localhost:$PORT/?access_token=\$access_token;
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
    
    # Pass the access token to Node-RED
    set \$access_token "";
    if (\$arg_access_token) {
        set \$access_token \$arg_access_token;
    }
    proxy_pass http://localhost:$PORT/ui/?access_token=\$access_token;
    add_header X-Frame-Options "SAMEORIGIN";
    add_header Content-Security-Policy "frame-ancestors 'self'";
}
EOF

# Reload Nginx to apply changes
sudo nginx -s reload

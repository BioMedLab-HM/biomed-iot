#!/bin/bash

# update_nginx.sh
# Parameters:  - Path Segment,  - Port

PATH_SEGMENT=
PORT=
NGINX_CONF_PATH="/etc/nginx/conf.d/nodered_locations/"

# Create or overwrite the Nginx configuration for the given path segment
cat >  <<EOF
location /nodered// {
    proxy_set_header X-Frame-Options "";
    proxy_hide_header X-Frame-Options;
    proxy_http_version 1.1;
    rewrite ^/nodered//(.*)$ /$1 break;
    proxy_set_header Upgrade $\http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_pass http://localhost:;
    add_header X-Frame-Options "SAMEORIGIN";  # instance only displayed within an iframe
    add_header Content-Security-Policy "frame-ancestors 'self'";  # restricts embedding to the same origin as the page
}

location ~* ^/admin/(.+\.(css|js)) {
    rewrite ^/static/contents/$1 break;
    proxy_pass http://localhost:;
  }
EOF

# Reload Nginx
sudo nginx -s reload

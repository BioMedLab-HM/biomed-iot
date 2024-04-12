#!/bin/sh

# Get passed parameter
DOMAIN=$1

# Define nginx server block template:
# Certbot updates the server blocks automatically. 
# Nevertheless, listen 443, redirect are prepared here to include custom tls-params.conf

cat << EOF
# Direct MQTT traffic through nginx as reverse proxy
#load_module modules/ngx_stream_module.so;
stream {
    server {
        listen 8883 ssl; # Listen for MQTT over TLS
        proxy_pass localhost:1885; # Forward to Mosquitto's listener

        # IMPORTANT: Please check if the following two lines contain  the correct file path to the actual files after installation
        # ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
        # ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

        include snippets/tls-params.conf;   # contains additional params
    }
}
EOF

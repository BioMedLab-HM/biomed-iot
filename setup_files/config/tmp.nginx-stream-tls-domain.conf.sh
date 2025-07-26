#!/bin/sh

# Get passed parameter
DOMAIN=$1

# Define nginx server block template:
# Certbot updates the server blocks automatically. 
# Nevertheless, listen 443, redirect are prepared here to include custom tls-params.conf

cat << EOF
# Direct MQTT traffic through nginx as reverse proxy
#load_module modules/ngx_stream_module.so;  # is already loaded by default
stream {
    server {
        listen 8883 ssl; # Listen for MQTT over TLS
        proxy_pass localhost:1884; # Forward to Mosquitto's listener

        # IMPORTANT: Please check if the following two lines contain the correct file path to the actual files after installation
        ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

        # SSL Params
        ssl_protocols TLSv1.3;                # Use TLSv1.3 (ensure nginx >= 1.13.0; otherwise, opt for TLSv1.2)
        ssl_prefer_server_ciphers on;         # Prioritize server's cipher order over client's
        # ssl_dhparam /etc/nginx/dhparam.pem; # NOT NEEDED BECAUSE OF ECDSA Path to Diffie-Hellman param. file for enhanced security. Generate : openssl dhparam -out /etc/nginx/dhparam.pem 3072
        ssl_ciphers EECDH+AESGCM:EDH+AESGCM;  # Define the list of encryption ciphers the server supports
        ssl_ecdh_curve secp384r1;             # Specify elliptic curve for ECDH key exchange, ensure nginx >= 1.1.0
        ssl_session_timeout  10m;             # Time after which SSL sessions expire and renegotiation is required
        ssl_session_cache shared:SSLStream:10m;  # Unique name SSLStream needed     # Share the SSL session cache across all worker processes for faster SSL handshakes
        ssl_session_tickets off;              # Disable session tickets for PFS (Perfect Forward Secrecy), ensure nginx >= 1.5.9
    }
}
EOF

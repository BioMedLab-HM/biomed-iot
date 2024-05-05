#!/bin/sh

# Get passed parameter
USERNAME=$1
SETUP_DIR=$2

# Define gunicorn.service template
cat << EOF
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=$USERNAME
Group=www-data
WorkingDirectory=$SETUP_DIR/biomed_iot
ExecStart=$SETUP_DIR/biomed_iot/venv/bin/gunicorn \
    --access-logfile - \
    --workers 3 \
    --bind unix:/run/gunicorn.sock \
    biomed_iot.wsgi:application

[Install]
WantedBy=multi-user.target
EOF
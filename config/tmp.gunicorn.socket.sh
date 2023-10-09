#!/bin/sh

# Get passed parameter
VAR=$1

# Define gunicorn.socket template
cat << EOF
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target

EOF
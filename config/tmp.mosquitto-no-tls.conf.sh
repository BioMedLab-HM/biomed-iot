#!/bin/sh

# Get passed parameter
DYNSEC_PLUGIN_PATH=$1

# Define mosquitto-no-tls.conf template
cat << EOF
# Explicitly disabled when using dynamic security plugin according to mosquitto website manual
per_listener_settings false

# Listener on port 1883
listener 1883

allow_anonymous false

plugin $DYNSEC_PLUGIN_PATH
plugin_opt_config_file /etc/mosquitto/dynamic-security.json

acl_file /etc/iotree/.acl
EOF
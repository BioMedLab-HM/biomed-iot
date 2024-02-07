#!/bin/sh

# Get passed parameter
DYNSEC_PLUGIN_PATH=$1

# Define mosquitto-no-tls.conf template
cat << EOF
# Mosquitto broker configuration for IoTree42 Platform
# Manual for this file, see https://mosquitto.org/man/mosquitto-conf-5.html

# Explicitly disabled when using dynamic security plugin according to mosquitto website manual
per_listener_settings false

# Listener on port 1883 only for clients on localhost
listener 1883 localhost
# Only allow clients to connect with known credentials
allow_anonymous false

# Listener on port 1884 for TLS secured external connections (through nginx reverse proxy)
listener 1884 localhost
allow_anonymous false

# Autosave broker in-memory database to disk 
autosave_interval 300  

# To remember retained messages after broker restart.
persistence true

# Allowed number of simultaneously connected clients (-1 is infinite) 
max_connections -1

# Max. number of outgoing QoS 1/2 messages that can be transmitted simultaneously
max_inflight_messages 100

plugin $DYNSEC_PLUGIN_PATH
plugin_opt_config_file /etc/mosquitto/dynamic-security.json
EOF
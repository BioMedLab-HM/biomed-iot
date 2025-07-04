#!/bin/sh

# Get passed parameter
DYNSEC_PLUGIN_PATH=$1

# Define mosquitto-no-tls.conf template
cat << EOF
# Mosquitto broker configuration for Biomed IoT Platform
# Manual for this file, see https://mosquitto.org/man/mosquitto-conf-5.html

# Explicitly disabled when using dynamic security plugin according to mosquitto website manual
per_listener_settings false

# listener for port 1884 on localhost 
listener 1884 localhost

# listener on port 1885 on docker network host address
listener 1885 172.17.0.1

# Only allow clients to connect with known credentials
allow_anonymous false

# Replace the clientid that a client connected with its username. Since usernames are unique, 
# this makes it impossible to have two clients with the same client id, kicking each other out.
use_username_as_clientid true

# Autosave broker in-memory database to disk (contains information about client subscriptions, retained messages, etc.)
# A lower number in seconds reduces data losss in case of a broker crash but increases disk I/O.
# Only works with 'persistence true'
autosave_interval 300

# To remember retained messages after broker restart.
persistence true

# Allowed number of simultaneously connected clients (-1 is infinite) 
max_connections -1

# The maximum number of QoS 1 or 2 messages to hold in the queue (per client) above those 
# messages that are currently in flight. Defaults to 1000. Set to 0 for no maximum (not recommended)
max_queued_messages 10000

# Max. number of outgoing QoS 1/2 messages that can be transmitted (be in-flight) without 
# acknoledgements from the client. This helps avoid overwhelming clients with too many messages at once, 
# particularly in unreliable network conditions. A value of 1 guarantees in Order transmission.
max_inflight_messages 1

plugin $DYNSEC_PLUGIN_PATH
plugin_opt_config_file /var/lib/mosquitto/dynamic-security.json
EOF

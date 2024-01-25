#!/bin/sh

# Get passed parameter
VAR_1=$1

# Define dynamic-security.json template
# see: https://mosquitto.org/documentation/dynamic-security/

# TODO:
# Clients:
# Groups
# Roles
# - admin
# - djControle
# - djSend
# - mqttInToDB
# - mqttOutToDB
# - user


cat << EOF
# TODO
{
	"defaultACLAccess":	{
		"publishClientSend":	false,
		"publishClientReceive":	false,
		"subscribe":	false,
		"unsubscribe":	false
	},
	"clients":	[],
	"groups":	[],
	"roles":	[]
}
EOF
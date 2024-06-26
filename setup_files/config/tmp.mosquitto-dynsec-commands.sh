#!/bin/sh

# Get passed parameter
MQTT_IN_TO_DB_USER=$1
MQTT_IN_TO_DB_PW=$2
MQTT_OUT_TO_DB_USER=$3
MQTT_OUT_TO_DB_PW=$4

# Define dynamic-security.json commands
# see: https://github.com/eclipse/mosquitto/blob/master/plugins/dynamic-security/README.md
# For general information about the Mosquitto dynamic security plugin, 
# see: https://mosquitto.org/documentation/dynamic-security/

# TODO: ggf. Priorities von -1 auf 1 setzen?

cat << EOF
{
	"commands":[
		{
			"command": "setDefaultACLAccess",
			"acls":[
				{ "acltype": "publishClientSend", "allow": false },
				{ "acltype": "publishClientReceive", "allow": true },
				{ "acltype": "subscribe", "allow": false },
				{ "acltype": "unsubscribe", "allow": true }
			]
		},
		{
			"command": "createRole",
			"rolename": "mqttInToDB",
			"acls": [
				{
					"acltype":	"publishClientReceive",
					"topic":	"input/#",
					"priority":	1,
					"allow":	true
				}, {
					"acltype":	"subscribePattern",
					"topic":	"input/#",
					"priority":	1,
					"allow":	true
				}, {
					"acltype":	"unsubscribePattern",
					"topic":	"input/#",
					"priority":	1,
					"allow":	true
				}
			]
		},
		{
			"command": "createRole",
			"rolename": "mqttOutToDB",
			"acls": [
				{
					"acltype":	"publishClientReceive",
					"topic":	"output/#",
					"priority":	1,
					"allow":	true
				}, {
					"acltype":	"subscribePattern",
					"topic":	"output/#",
					"priority":	1,
					"allow":	true
				}, {
					"acltype":	"unsubscribePattern",
					"topic":	"output/#",
					"priority":	1,
					"allow":	true
				}
			]
		},
		{
			"command": "createClient",
			"username": "$MQTT_IN_TO_DB_USER",
			"password": "$MQTT_IN_TO_DB_PW",
			"textname": "mqttInToDB",
			"roles": [
				{ "rolename": "mqttInToDB", "priority": -1 }
			]
		},
		{
			"command": "createClient",
			"username": "$MQTT_OUT_TO_DB_USER",
			"password": "$MQTT_OUT_TO_DB_PW",
			"textname": "mqttOutToDB",
			"roles": [
				{ "rolename": "mqttOutToDB", "priority": -1 }
			]
		}
	]
}
EOF

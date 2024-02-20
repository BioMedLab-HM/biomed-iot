#!/bin/sh

# Get passed parameter
DJ_MQTT_CONTROLE_USER=$1
DJ_MQTT_CONTROLE_PW=$2
MQTT_IN_TO_DB_USER=$3
MQTT_IN_TO_DB_PW=$4
MQTT_OUT_TO_DB_USER=$5
MQTT_OUT_TO_DB_PW=$6
USER_FOR_WEBSITE_ADMIN=$7
PW_FOR_WEBSITE_ADMIN=$8

# Define dynamic-security.json template
# see: https://mosquitto.org/documentation/dynamic-security/

# TODO: ggf. Priorities von -1 auf 1 setzen?

cat << EOF
{
	"commands":[
		{
			"command": "setDefaultACLAccess",
			"acls":[
				{ "acltype": "publishClientSend", "allow": false },
				{ "acltype": "publishClientReceive", "allow": false },
				{ "acltype": "subscribe", "allow": false },
				{ "acltype": "unsubscribe", "allow": false }
			]
		},
		{
			"command": "createRole",
			"rolename": "djControle",
			"acls": [
				{
					"acltype": "publishClientSend",
					"topic": "$CONTROL/dynamic-security/#",
					"priority": -1,
					"allow": true
				}
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
			"command": "createRole",
			"rolename": "$USER_FOR_WEBSITE_ADMIN",
			"acls": [
				{
					"acltype":	"publishClientSend",
					"topic":	"input/$USER_FOR_WEBSITE_ADMIN/#",
					"priority":	1,
					"allow":	true
				}, {
					"acltype":	"publishClientReceive",
					"topic":	"input/$USER_FOR_WEBSITE_ADMIN/#",
					"priority":	1,
					"allow":	true
				}, {
					"acltype":	"subscribePattern",
					"topic":	"input/$USER_FOR_WEBSITE_ADMIN/#",
					"priority":	1,
					"allow":	true
				}, {
					"acltype":	"unsubscribePattern",
					"topic":	"input/$USER_FOR_WEBSITE_ADMIN/#",
					"priority":	1,
					"allow":	true
				}, {
					"acltype":	"publishClientSend",
					"topic":	"output/$USER_FOR_WEBSITE_ADMIN/#",
					"priority":	1,
					"allow":	true
				}, {
					"acltype":	"publishClientReceive",
					"topic":	"output/$USER_FOR_WEBSITE_ADMIN/#",
					"priority":	1,
					"allow":	true
				}, {
					"acltype":	"subscribePattern",
					"topic":	"output/$USER_FOR_WEBSITE_ADMIN/#",
					"priority":	1,
					"allow":	true
				}, {
					"acltype":	"unsubscribePattern",
					"topic":	"output/$USER_FOR_WEBSITE_ADMIN/#",
					"priority":	1,
					"allow":	true
				}
			]
		},
		{
			"command": "createClient",
			"username": "$DJ_MQTT_CONTROLE_USER",
			"password": "$DJ_MQTT_CONTROLE_PW",
			"textname": "djControle",
			"roles": [
				{ "rolename": "djControle", "priority": -1 }
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
		},
		{
			"command": "createClient",
			"username": "$USER_FOR_WEBSITE_ADMIN",
			"password": "$PW_FOR_WEBSITE_ADMIN",
			"textname": "websiteUser",
			"roles": [
				{ "rolename": "$USER_FOR_WEBSITE_ADMIN", "priority": -1 }
			]
		}
	]
}
EOF

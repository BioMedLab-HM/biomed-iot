#!/bin/sh

# Get passed parameter
VAR_1=$1  # TODO

# Define dynamic-security.json template
# see: https://mosquitto.org/documentation/dynamic-security/

# TODO:
# Clients: (username, password (salt?, iterations?), roles, )
# - admin
# - djControle
# - djSend
# - mqttInToDB
# - mqttOutToDB
# - <> (has role userDevice)
# Groups
# Roles
# - admin
# - djControle
# - djSend
# - mqttInToDB
# - mqttOutToDB
# - userDevice


cat << EOF
# TODO
{
	"defaultACLAccess":	{
		"publishClientSend":	false,
		"publishClientReceive":	false,
		"subscribe":	false,
		"unsubscribe":	false
	},
	"clients":	[{
			"username":	"admin",
			"textname":	"Dynsec admin user",
			"roles":	[{
					"rolename":	"admin"
				}],
			"password":	"TODO",
			"salt":	"TODO",
			"iterations":	101
		}],
	"groups":	[],
	"roles":	[{
			"rolename":	"admin",
			"acls":	[{
					"acltype":	"publishClientSend",
					"topic":	"$CONTROL/dynamic-security/#",
					"priority":	0,
					"allow":	true
				}, {
					"acltype":	"publishClientReceive",
					"topic":	"$CONTROL/dynamic-security/#",
					"priority":	0,
					"allow":	true
				}, {
					"acltype":	"publishClientReceive",
					"topic":	"$SYS/#",
					"priority":	0,
					"allow":	true
				}, {
					"acltype":	"publishClientReceive",
					"topic":	"#",
					"priority":	0,
					"allow":	true
				}, {
					"acltype":	"subscribePattern",
					"topic":	"$CONTROL/dynamic-security/#",
					"priority":	0,
					"allow":	true
				}, {
					"acltype":	"subscribePattern",
					"topic":	"$SYS/#",
					"priority":	0,
					"allow":	true
				}, {
					"acltype":	"subscribePattern",
					"topic":	"#",
					"priority":	0,
					"allow":	true
				}, {
					"acltype":	"unsubscribePattern",
					"topic":	"#",
					"priority":	0,
					"allow":	true
				}]
		}]
}
EOF
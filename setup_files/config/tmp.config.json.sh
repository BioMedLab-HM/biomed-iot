#!/bin/sh

# Get passed parameter
# TODO: USERNAME entfernen?
USERNAME=$1
HOSTIP=$2
DOMAIN=$3
ADMINMAIL=$4
SENDMAIL=$5
SENDPASS=$6
DJANGOKEY=$7
POSTGRESUSER=$9
POSTGRESPASS=$10
# Add variables

# Define config.json template
# TODO: Nutzernamen im Template vs Zufallsgeneriert?
# TODO: Ab Mosquitto oben Variablen hinzufügen
cat << EOF
{       
        "HOST_IP":"$HOSTIP",
        "DOMAIN":"$DOMAIN",

        "SENDING_MAIL":"$SENDMAIL",
        "SENDING_PASS":"$SENDPASS",
        "ADMIN_MAIL":"$ADMINMAIL",
        "DJANGO_SECRET_KEY":"$DJANGOKEY",

        "POSTGRES_NAME":"biomed_iot_db",
        "POSTGRES_USER":"biomed_iot_user",
        "POSTGRES_PASS":"$POSTGRESPASS"
        
        "BROKER_PORT":1883,
        "BROKER_ADDRESS":"localhost,
	"MQTT_INFLUX_USER":"mqttodb,
	"MQTT_INFLUX_USER_PASS":$MQTT_INFLUX_USER_PASS,
        "MQTT_SEND_USER":djsend,
        "MQTT_SEND_PASS":$MQTT_SEND_PASS,
        "MQTT_CONTROLE_USER":djcontrole,
        "MQTT_CONTROLE_PASS":$MQTTCONTROLEPASS,
        "MQTT_DYNSEC_ADMIN":mqttadmin,
        "MQTT_DYNSEC_PASS":$MQTTDYNSECPASS,
}
EOF
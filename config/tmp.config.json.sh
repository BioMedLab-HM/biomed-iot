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
POSTGRESPASSWORD=$10

# Define config.json template
cat << EOF
{       
        "SENDING_MAIL":"$SENDMAIL",
        "SENDING_PASS":"$SENDPASS",

        "ADMIN_MAIL":"$ADMINMAIL",

        "DJANGO_SECRET_KEY":"$DJANGOKEY",

        "HOST_IP":"$HOSTIP",
        "DOMAIN":"$DOMAIN",

        "POSTGRES_NAME":"dj_iotree_db",
        "POSTGRES_USER":"dj_iotree_user",
        "POSTGRES_PASSWORD":"$POSTGRESPASSWORD"
}
EOF
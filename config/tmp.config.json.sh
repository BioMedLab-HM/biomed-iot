#!/bin/sh

# define parameters which are passed in.
# TODO: USERNAME entfernen?
USERNAME=$1
HOSTIP=$2
HOSTNAME=$3
ADMINMAIL=$4
SENDMAIL=$5
SENDPASS=$6
DJANGOKEY=$7
POSTGRESUSER=$9
POSTGRESPASSWORD=$10

# config.json template definition
cat << EOF
{       
        "SENDING_MAIL":"$SENDMAIL",
        "SENDING_PASS":"$SENDPASS",

        "ADMIN_MAIL":"$ADMINMAIL",

        "DJANGO_SECRET_KEY":"$DJANGOKEY",

        "HOST_IP":"$HOSTIP",
        "HOSTNAME":"$HOSTNAME",

        "POSTGRES_NAME":"dj_iotree_db",
        "POSTGRES_USER":"dj_iotree_user",
        "POSTGRES_PASSWORD":"$POSTGRESPASSWORD"
}
EOF
#!/bin/bash
# Parameters
IP=$1
HOSTNAME=$2

# Create the OpenSSL configuration file with dynamic values
# To make curl command accept the certificate put under [ req_ext ]: basicConstraints=critical,CA:TRUE,pathlen:1 
# --> turns out to be not working

cat << EOF
[ req ]
default_bits       = 2048
default_md         = sha256
prompt             = no
distinguished_name = req_distinguished_name
req_extensions     = req_ext

[ req_distinguished_name ]
C  = DE
ST = Bavaria
L  = Munich
O  = BioMedLab
OU = Biomed-IoT
CN = $HOSTNAME

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1   = $HOSTNAME
IP.1    = $IP
EOF

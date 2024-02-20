#!/bin/bash

# Set your variables
DJANGO_ADMIN_NAME=$1
CLIENT_NAME_FOR_WEBSITE_ADMIN=$2
CLIENT_PW_FOR_WEBSITE_ADMIN=$3

cat << EOF
from django.contrib.auth import get_user_model
from users.models import MosquittoClientData

User = get_user_model()

admin_user = User.objects.get(username="$DJANGO_ADMIN_NAME")

# Create (or update) the MosquittoClientData for the admin user
mosquitto_client_data, created = MosquittoClientData.objects.update_or_create(
    user=admin_user,
    defaults={
        'username': "$CLIENT_NAME_FOR_WEBSITE_ADMIN",
        'password': "$CLIENT_PW_FOR_WEBSITE_ADMIN",
        # Add additional fields as necessary
    }
)

if created:
    print(f"Created MQTT client data for website admin user")
else:
    print(f"Updated MQTT client data for website admin user")
EOF

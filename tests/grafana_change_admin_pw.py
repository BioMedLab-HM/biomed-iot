# Test the Grafana user password reset api

import requests
from requests.auth import HTTPBasicAuth

old_password = ""
new_password = ""
grafana_host = "localhost"
grafana_port = 3000
admin_user = "admin"

url = f"http://{grafana_host}:{grafana_port}/api/user/password"

headers = {'Content-Type': 'application/json'}
payload = {
    "oldPassword": old_password,
    "newPassword": new_password,
    "confirmNew": new_password
}

response = requests.put(
    url,
    json=payload,
    headers=headers,
    auth=HTTPBasicAuth(admin_user, old_password)
)

if response.status_code == 200:
    print("Password changed successfully.")
else:
    print(f"Failed to change password. Status code: {response.status_code}, Response: {response.text}")

#!/usr/bin/env bash

logo_header="
 ______   _                           _    _      _______ 
(____  \ (_)                         | |  | |    (_______)
 ____)  ) _   ___   ____   _____   __| |  | |  ___  | |    
|  __  ( | | / _ \ |    \ | ___ | / _  |  | | / _ \ | |   
| |__)  )| || |_| || | | || ____|( (_| |  | || |_| || |   
|______/ |_| \___/ |_|_|_||_____) \____|  |_| \___/ |_|   
"

echo -e "\n\n$logo_header\n\n"

# 1. Prompt for details
read -rp "Enter the domain (example.com) of Biomed IoT: " hostname
read -rp "Enter the 'Name' for your gateway (as shown on the 'Devices' page): " gatewayname
read -srp "Enter the corresponding 'username' for your gateway (as shown on the 'Devices' page): " mqtt_username; echo
read -srp "Enter the corresponding 'password' for your gateway (as shown on the 'Devices' page): " mqtt_password; echo
read -srp "Enter your personal topic-id (as shown on the 'Message & Topic Structure' page): " topic_id; echo

# 2. Detect the real user, even if run via sudo
if [ -n "$SUDO_USER" ]; then
  username="$SUDO_USER"
else
  username="$(whoami)"
fi

# 3. Update & install
sudo apt update -y
sudo apt install -y mosquitto mosquitto-clients

# 4. Backup default config, leave it to include conf.d/*
sudo cp /etc/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf.backup

# 5. Drop in our bridge config
sudo mkdir -p /etc/mosquitto/conf.d
sudo tee /etc/mosquitto/conf.d/biomed_gateway.conf > /dev/null <<EOL
# Biomed IoT Gateway Configuration
listener 1883 0.0.0.0
allow_anonymous true

connection ${gatewayname}
address ${hostname}:8883

bridge_cafile /etc/ssl/certs/ISRG_Root_X1.pem

remote_username ${mqtt_username}
remote_password ${mqtt_password}
cleansession true

# Outgoing messages: in/ → in/${topic_id}/
topic # out 2 in/ in/${topic_id}/

# Incoming messages: out/ → out/${topic_id}/${gatewayname}/
topic # in  2 out/ out/${topic_id}/${gatewayname}/
EOL

# 6. Permissions
sudo chmod 644 /etc/mosquitto/conf.d/biomed_gateway.conf

# 7. Schedule status cronjob without wiping existing jobs
cron_job="* * * * * mosquitto_pub -t in/devicestatus -m '{\"$gatewayname\":1}' -h localhost -p 1883"
{
  crontab -l -u "$username" 2>/dev/null | grep -Fv "$cron_job"
  echo "$cron_job"
} | crontab -u "$username" -

# 8. Enable & restart Mosquitto
sudo systemctl enable mosquitto.service
sleep 1
sudo systemctl restart mosquitto.service

# 9. Final instructions
cat <<MSG
_____


Your IoT-Gateway is set up. Please reboot.

After reboot:
  • Go to 'Automate' (Node-RED) on the Biomed-IoT Platform.
  • Use a green Debug Node to look for a status message '{"$gatewayname":1}' under 'in/<your-topic-id>/devicestatus'.
  • If you see it, your gateway is successfully connected.
  • You may run also run the script 'publish_cpu_temp.sh' to test publishing data with 'bash publish_cpu_temp.sh'.

If you run into issues:
  • Check broker status: sudo systemctl status mosquitto
  • Verify /etc/mosquitto/conf.d/biomed.conf for correct credentials, broker address, gateway name, and topic id.

MSG

#!/bin/bash

logo_header="
 ______   _                           _    _      _______ 
(____  \ (_)                         | |  | |    (_______)
 ____)  ) _   ___   ____   _____   __| |  | |  ___   _    
|  __  ( | | / _ \ |    \ | ___ | / _  |  | | / _ \ | |   
| |__)  )| || |_| || | | || ____|( (_| |  | || |_| || |   
|______/ |_| \___/ |_|_|_||_____) \____|  |_| \___/ |_|   
"

echo
echo
echo "$logo_header"
echo
echo
echo "Enter the hostname (domain or IP-address) of Biomed IoT"
read hostname
echo
echo "Enter the 'Name' for your gateway (device), you created on the 'Device List' page of Biomed IoT"
read gatewayname
echo 
echo "Enter the corresponding 'username' for your device. (input is hidden for safety)"
read -s mqtt_username
echo
echo "Enter the corresponding 'password' for your device. (input is hidden for safety)"
read -s mqtt_password
echo
echo "Enter your personal topic-id from the 'Message & Topic Structure' page of Biomed IoT (input is hidden for safety)"
read -s topic_id
echo

sudo apt-get -y update
sudo apt -y install mosquitto mosquitto-clients
sudo mv /etc/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf.backup

sudo tee -a /etc/mosquitto/mosquitto.conf > /dev/null <<EOL
port 1883
allow_anonymous true
connection ${gatewayname}
address ${hostname}:8883
remote_password ${mqtt_password}
remote_username ${mqtt_username}
bridge_cafile /etc/mosquitto/certs/biomed-iot.crt
# For outgoing messages: rewrite topics from prefix "in/" to "in/${topic_id}/"
topic # out 2 in/ in/${topic_id}/
# For incoming messages: rewrite topics from prefix "out/" to "out/${topic_id}/${gatewayname}/"
topic # in 2 out/ out/${topic_id}/${gatewayname}/
EOL

sudo chmod -R 644 /etc/mosquitto/mosquitto.conf

sudo mkdir -p /etc/mosquitto/certs
sudo cp -r ./biomed-iot.crt /etc/mosquitto/certs/biomed-iot.crt

# Get the current user who runs the script
username=$(whoami)
sudo crontab -r -u $username
# Add a cron job to send an MQTT status message every minute
line="* * * * * mosquitto_pub -t in/devicestatus -m '{\"$gatewayname\":1}' -h localhost -p 1883"
(crontab -u $username -l; echo "$line") | sudo crontab -u $username -

# Restart Mosquitto to apply the new configuration
sleep 1
sudo systemctl restart mosquitto
sleep 1

# Display final messages
echo "Your IoT-Gateway is set up. Please reboot"
echo
echo "After reboot go to 'Automate' (Node-RED) on the Biomed-IoT Plattform and check if you can"
echo "see a status message '{\"$gatewayname\":1}' under the topic 'in/<your-topic-id>/devicestatus'."
echo
echo "If you have troubles:"
echo "Check with this command if the Mosquitto Broker is running properly: 'sudo systemctl status mosquitto'."
echo "Check the '/etc/mosquitto/mosquitto.conf' for correct 'remote_username', 'remote_password',"
echo "remote broker address, gateway name ('connection') and topic id."
echo

#!/bin/bash

echo
echo
cat << EOL
 ______   _                           _    _      _______ 
(____  \ (_)                         | |  | |    (_______)
 ____)  ) _   ___   ____   _____   __| |  | |  ___   _    
|  __  ( | | / _ \ |    \ | ___ | / _  |  | | / _ \ | |   
| |__)  )| || |_| || | | || ____|( (_| |  | || |_| || |   
|______/ |_| \___/ |_|_|_||_____) \____|  |_| \___/ |_|   
EOL

# Path to the mosquitto.conf file
mosquitto_conf_path="/etc/mosquitto/mosquitto.conf"

# Extract the gatewayname from the connection line
gatewayname=$(grep -i '^connection ' "$mosquitto_conf_path" | awk '{print $2}')

# Check if the gatewayname was found
if [ -n "$gatewayname" ]; then
    echo "Gateway name is: $gatewayname"
else
    echo "Gateway name not found in $mosquitto_conf_path"
fi

echo
echo "<<<-----   Publish Rasberry Pi CPU Temperature   ----->>>"
echo
echo "If you use a Raspvberry Pi as Gateway, this script sends current CPU temperature every 20 seconds."
echo "The message will be published on the IoT platform under topic"
echo "in/<your_topic_id>/$gatewayname/cputemp"
echo "Test it in another terminal window with this command, you should see the messages:"
echo "mosquitto_sub -h localhost -p 1883 -t "in/#""
echo
echo "You can stop this script by pressing Ctrl+C"
echo

while true
do
cputemp=$(cat /sys/class/thermal/thermal_zone0/temp)
cputemp=$((cputemp / 1000))
timestamp=$(date "+%s")
echo '{"cputemp":'$cputemp',"timestamp":'$timestamp'}'

# TOPIC_ID will be replaced with actual topic id during gateway setup
mosquitto_pub -h localhost -p 1883 -t in/$gatewayname/cputemp -m '{"cputemp":'$cputemp',"timestamp":'$timestamp'}'

sleep 20
done

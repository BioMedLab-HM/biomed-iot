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

echo
echo "<<<-----   Publish RPi CPU Temperature   ----->>>"
echo
echo "This script sends the Raspberry Pi's current CPU temperature every 20 seconds."
echo "The message will be published under topic"
echo "sensorbase/in/<your_topic_id>/cputemp"
echo "Test it in another terminal window with this command, you shouldd see the messages:"
echo "mosquitto_sub -h localhost -p 1883 -t "sensorbase/#""
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
mosquitto_pub -h localhost -p 1883 -t sensorbase/in/TOPIC_ID/cputemp -m '{"cputemp":'$cputemp',"timestamp":'$timestamp'}'

sleep 20
done

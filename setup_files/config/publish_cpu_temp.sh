#!/bin/bash

logo_header = """
 ______   _                           _    _      _______ 
(____  \ (_)                         | |  | |    (_______)
 ____)  ) _   ___   ____   _____   __| |  | |  ___   _    
|  __  ( | | / _ \ |    \ | ___ | / _  |  | | / _ \ | |   
| |__)  )| || |_| || | | || ____|( (_| |  | || |_| || |   
|______/ |_| \___/ |_|_|_||_____) \____|  |_| \___/ |_|   
"""

echo
echo
echo $logo_header
echo
echo
echo "<<<-----   Publish RPi CPU Temperature   ----->>>"
echo "This script sends the Raspberryy Pi's current CPU temperature every 20 seconds."
echo "The message will be published under topic"
echo "sensorbase/in/<your_topic_id>/cputemp"

while true
do
cputemp=$(cat /sys/class/thermal/thermal_zone0/temp)
cputemp=$((cputemp / 1000))
timestamp=$(date "+%s")
echo '{"cputemp":'$cputemp',"timestamp":'$timestamp'}'
mosquitto_pub -h localhost -p 1883 -t sensorbase/in/TOPIC_ID/cputemp -m '{"cputemp":'$cputemp',"timestamp":'$timestamp'}'
sleep 20
done

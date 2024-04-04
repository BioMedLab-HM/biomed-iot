import paho.mqtt.client as mqtt
import os
import tomllib

with open("/etc/iotree/config.toml", "rb") as f:
    config = tomllib.load(f)

# MQTT Broker settings
BROKER_HOST = config['mosquitto']['BROKER_HOST']
BROKER_PORT = config['mosquitto']['BROKER_PORT']
DYNSEC_USER = config['mosquitto']['DYNSEC_USER']
DYNSEC_PASSWORD = config['mosquitto']['DYNSEC_PASSWORD']
DYNSEC_TOPIC = config['mosquitto']['DYNSEC_TOPIC']
MQTT_MESSAGE = '{"commands":[{"command":"getDefaultACLAccess"}]}'

def on_publish(client, userdata, mid):
    print(f"Message published with mid {mid}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

# Create MQTT client instance
client = mqtt.Client()

# Set username and password
client.username_pw_set(DYNSEC_USER, DYNSEC_PASSWORD)

# Assign callback functions
client.on_connect = on_connect
client.on_publish = on_publish

# Connect to the MQTT broker
client.connect(BROKER_HOST, BROKER_PORT)

# Publish a message
client.publish(DYNSEC_TOPIC, MQTT_MESSAGE)

# Disconnect from the MQTT broker
client.disconnect()

import paho.mqtt.client as mqtt
import time
import os
import tomllib

with open("/etc/iotree/config.toml", "rb") as f:
    config = tomllib.load(f)

# MQTT Broker settings
BROKER_HOST = config["mosquitto"]["BROKER_HOST"]
BROKER_PORT = config["mosquitto"]["BROKER_PORT"]
DYNSEC_USER = config["mosquitto"]["DYNSEC_USER"]
DYNSEC_PASSWORD = config["mosquitto"]["DYNSEC_PASSWORD"]
DYNSEC_TOPIC = config["mosquitto"]["DYNSEC_TOPIC"]
DYNSEC_RESPONSE_TOPIC = config["mosquitto"]["DYNSEC_RESPONSE_TOPIC"]

received_flag = False


# Callback function for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(DYNSEC_RESPONSE_TOPIC)  # Subscribe to the topic


# Callback function for when a PUBLISH message is received from the server
def on_message(client, userdata, msg):
    global received_flag
    received_flag = True
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    client.disconnect()  # Disconnect after receiving a message


client = mqtt.Client()
client.username_pw_set(DYNSEC_USER, DYNSEC_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_HOST, BROKER_PORT, 60)

client.loop_start()  # Start the loop in a separate thread
runtime = 100
timeout = time.time() + runtime  # 1 second from now
while True:
    if received_flag or time.time() > timeout:
        break

client.loop_stop()  # Stop the loop
client.disconnect()  # Disconnect the client

if not received_flag:
    print("Timeout! No message received within {runtime} second.")

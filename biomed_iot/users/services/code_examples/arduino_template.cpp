/* 
 * esp32 MQTT client
 */

#include <stdio.h>
#include <time.h>
#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h> // https://pubsubclient.knolleary.net
#include <WiFiUdp.h>
#include <NTPClient.h> // https://www.arduino.cc/reference/en/libraries/ntpclient/

// UDP-Connection and NTP-Client for Unix-time
#define NTP_OFFSET   60 * 60      // Offset according to time zone (in seconds)
#define NTP_INTERVAL 60 * 1000    // In miliseconds
#define NTP_ADDRESS  "europe.pool.ntp.org"
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, NTP_ADDRESS, NTP_OFFSET, NTP_INTERVAL);

// WIFI & MQTT:
const char   *SSID            = "<YOUR_WIFI_SSID_HERE>";
const char   *PASSWORD        = "<YOUR_WIFI_PASSWORD_HERE>";
const char   *HOSTNAME        = "<THE_HOSTNAME_OR_IP_OF_BIOMED_IOT>";
const char   *MQTT_SERVER     = "<THE_IP_OF_BIOMED_IOT>";
const short   MQTT_PORT       = 1883;
const char   *MQTT_TEMP_TOPIC = "in/<YOUR_TOPIC_ID>/esp32/temperature";
const char   *MQTT_PING_TOPIC = "in/<YOUR_TOPIC_ID>/esp32/ping";
const char   *WILL_TOPIC      = "in/<YOUR_TOPIC_ID>/esp32/will";  // OPTIONAL
const boolean WILL_RETAIN     = false;
// About QoS see: http://www.steves-internet-guide.com/understanding-mqtt-qos-levels-part-1/
const int     QOS             = 0;
const char   *WILL_MESSAGE    = "0";  // 0 signals device is disconnected
const int     SLEEP_TIME_S    = 5000;  // the send interval in milliseconds
WiFiClient    esp32Client;
PubSubClient  client(esp32Client);

// Function prototypes
void reconnect();
void initWiFi(); 

void setup() {
  Serial.begin(115200); // start serial interface (UART)
  initWiFi();  // start WiFi connection

  // configure MQTT client and connect to broker
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.connect(HOSTNAME, NULL, NULL, WILL_TOPIC, QOS, WILL_RETAIN, WILL_MESSAGE, false);
  client.setKeepAlive(SLEEP_TIME_S + 5000);
  if (!client.connected()) {
    reconnect();
  }

  timeClient.begin(); // initalize client that gets current unix epoch time
}


void loop() {
  if (!client.connected()) {
    reconnect();
  }
  
  // get UNIX epoch time (seconds since 1.1.1970)
  timeClient.update();
  unsigned long epochTime =  timeClient.getEpochTime();

  // Read your sensordata.
  float temp = 42; // Here just a random temperature value

  // build json data and publish mock temp data to topic
  char payload[200];  // adjust according to message size
  sprintf(payload, "{\"temp\":%.1f,\"time\":%lu}", temp, epochTime);
  client.publish(MQTT_TEMP_TOPIC, payload);

  // publish 1 to ping topic
  sprintf(payload, "1");
  client.publish(MQTT_PING_TOPIC, payload);

  // print data to UART 
  Serial.print("Temperature = ");
  Serial.print(temp);
  Serial.printf("%cC   ", char(176)); // °C
  Serial.println();

  delay(SLEEP_TIME_S); // sensor measurement intervall
}

/**
 * Start WiFi
 */
void initWiFi() {
  WiFi.mode(WIFI_STA);        // set stationary mode
  WiFi.begin(SSID, PASSWORD); // start WiFi with credentials
  Serial.print("Connecting to WiFi ..");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(1000);
  }
}

/**
 * Attempt reconnection to the MQTT broker and subscription
 * to the MQTT topic indefinitely
 */
void reconnect() {
  while (!client.connected()) {
    String clientId = WiFi.getHostname();
    if (!client.connect(clientId.c_str())) {
      delay(2000);
    }
  }
}

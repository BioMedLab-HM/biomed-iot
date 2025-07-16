/* THIS VERSION IS FOR USE WITHOUT A BIOMED IOT GATEWAY
 * 
 * Example Code for Biomed IoT Device using 
 * - an ESP32 microcontroller
 * - a DHT22 temperature and humidity sensor on the A0 pin of your ESP32
 * 
 * To finish this code modify the following in the code below:
 * - wifi_ssid (enter your WiFi name)
 * - wifi_password (enter your WiFi password)
 * - mqtt_server (enter your Biomed IoT server IP address or domain name)
 * - mqtt_username and mqtt_password (enter the device credentials you created on the Biomed IoT platform)
 * - YOUR_TOPIC_ID (substitute it with your actual personal topic-id)
 * - DHTPIN (Adjust its value to the pin you used for your hardware setup)
 * - ALSO: if you want to change the sensors or the name for their values or the device name in the status message
 *         adjust the json message in the sections 'Publish values to MQTT...' and 'Send devicestatus 1'.
 *
 * For hardware setup and further help, visit: 
 * https://randomnerdtutorials.com/esp32-dht11-dht22-temperature-humidity-sensor-arduino-ide/
 */

#include <WiFi.h>          // Library for WiFi
#include <PubSubClient.h>  // Library for MQTT
#include <time.h>
#include "DHT.h"           // Library for DHT sensors

#define wifi_ssid          "YOUR_WIFI_NAME"
#define wifi_password      "YOUR_WIFI_PASSWORD"

#define mqtt_server        "BIOMED_IOT_SERVER_IP_OR_DOMAIN"
#define mqtt_username      "YOUR_DEVICE_USERNAME"
#define mqtt_password      "YOUR_DEVICE_PASSWORD"

#define temperature_topic  "in/YOUR_TOPIC_ID/esp32/temperature/"
#define humidity_topic     "in/YOUR_TOPIC_ID/esp32/humidity/" 
#define devicestatus_topic "in/YOUR_TOPIC_ID/devicestatus"

#define DHTPIN 4           // DHT Pin 
#define DHTTYPE DHT22      // DHT 22  (AM2302)

DHT dht(DHTPIN, DHTTYPE);      
WiFiClient espClient;
PubSubClient client(espClient);


void setup() {
  Serial.begin(115200);
  setup_wifi();
  
  client.setServer(mqtt_server, 1883);  // Configure MQTT connection
  if (!client.connected()) {
    reconnect();
  }
  dht.begin();
}

void loop() { 
  if (!client.connected()) { 
    reconnect(); 
  } 

  if (client.connected()){ 

    // Read sensor values
    float temperature = dht.readTemperature(); 
    float humidity = dht.readHumidity();

    // Publish values to MQTT topics and print to serial connection for debugging
    if (!isnan(temperature)){
      String payload = "{\"temperature\":" + String(temperature) + "}";
      client.publish(temperature_topic, String(payload).c_str(), true);
      Serial.println(String(temperature_topic) + ": " + payload); 
    }

    if (!isnan(humidity)){
      String payload = "{\"humidity\":" + String(humidity) + "}"; 
      client.publish(humidity_topic, String(payload).c_str(), true);
      Serial.println(String(humidity_topic) + payload); 
    }

    // Send devicestatus 1
    String payload = "{\"esp32\":" + String(1) + "}"; 
    client.publish(devicestatus_topic, String(payload).c_str(), true);
    Serial.println(String(devicestatus_topic) + payload);
    
  }
  
  // Wait for 10 seconds 
  delay (10000);
} 


void setup_wifi() {
  Serial.println();
  Serial.print("[WiFi] Connecting to ");
  Serial.println(wifi_ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifi_ssid, wifi_password);
  
  // Will try for about 10 seconds (20x 500ms)
  int tryDelay = 500;
  int numberOfTries = 20;

  // Wait for the WiFi event
  while (true) {
    switch(WiFi.status()) {
      case WL_NO_SSID_AVAIL:
        Serial.println("[WiFi] SSID not found");
        break;
      case WL_CONNECT_FAILED:
        Serial.print("[WiFi] Failed - WiFi not connected! Reason: ");
        return;
        break;
      case WL_CONNECTION_LOST:
        Serial.println("[WiFi] Connection was lost");
        break;
      case WL_SCAN_COMPLETED:
        Serial.println("[WiFi] Scan is completed");
        break;
      case WL_DISCONNECTED:
        Serial.println("[WiFi] WiFi is disconnected");
        break;
      case WL_CONNECTED:
        Serial.println("[WiFi] WiFi is connected!");
        Serial.print("[WiFi] IP address: ");
        Serial.println(WiFi.localIP());
        return;
        break;
      default:
        Serial.print("[WiFi] WiFi Status: ");
        Serial.println(WiFi.status());
        break;
      }
      delay(tryDelay);
          
    if(numberOfTries <= 0){
      Serial.print("[WiFi] Failed to connect to WiFi!");
      // Use disconnect function to force stop trying to connect
      WiFi.disconnect();
      ESP.restart();
      return;
    } else {
      numberOfTries--;
    }
  }
}


//Reconnect to wifi if connection is lost
void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT broker ...");
    if (client.connect("ESP32Client", mqtt_username, mqtt_password)) {
      Serial.println("OK");
    } else {
      Serial.print("[Error] Not connected: ");
      Serial.print(client.state());
      Serial.println("Wait 5 seconds before retry.");
      delay(5000);
    }
  }
}

# Biomed IoT - User Manual

This is the Biomed IoT User Manual. The installation instructions can be found in the [README file](README.md). 

Dieses Handbuch erklärt anhand eines einfachen Anwendungsbeispiel den Umgang mit der Biomed IoT Plattform. Du lernst wie Du:
- Temperatur- und Luftfeuchtedaten eines ESP32 Mikrocontrollers mit DHT 22 Sensor an die Plattform sendest
- diese Daten mit Node-RED in der Datenbank speicherst
- in Nodered eine Automation in Node-RED erstellst
- die Daten in Grafana visualisierst
- die Daten in Grafana als csv-Datei zum Download exportierst
- die Daten wieder aus der Datenbank löscht

Das Handbuch wird in Zukunft erweitert um weitere Funktionen der Plattform zu erklären.

## Content
- [Registration and Login](#Registration-and-Login)
- [MQTT Devices](#Performance-Testing)
    - [Requirements](#Requirements)
    - [Setup](#Setup)
    - [Optional Biomed IoT Gateway](#Troubleshooting)
- [How it works](#How-it-works)
- [How to use](#How-to-use)

## Registration and Login
Click on 'User' and then on 'Register' on the website menu bar.
Fill the form with all necessary data. The password needs to comply with the rules for safe passwords, listed there.
If Email validation is active (e.g. when Biomed IoT runs on the internet) you will receive an email with a verification link. In this case you need to click this link before you can log in with your email and password.

## Link Device to the platform
Data can be sent to the platform directly (recommended when the platform is running on a server in your local network)
or indirectly by sending data to a local Biomed IoT gateway that forwards the message to the platform with encryption (recommended if the Biomed IoT platform is running on an internet server)

### Variant 1: With Gateway
Go to gateway setup page and follow the instructions there.
Use Code Example for device (ESP32) (gateway version)

### Variant 2: Without Gateway
Create Device credentials and get personal topic ID.
Use Code Example for device (ESP32) (non-gateway version) and fill in credentials and use personal topic ID for the topic.

## Create Automations and Save Data to the Database (Node-RED)
Click 'Automate' on the website menu and read the instructions there.
Once you opened Node-RED and see the Flow Editor and made the described modifications to the nodes, your temperature and humidity data is safed to the database. Automation...erwähnen

## Visualize with Grafana
Click on 'Visualize' on the website menu.
First create a new dashboard and add a visualization
1. Click on 'Dashboards' (menu on the left)
2. Click the blue button saying 'New' on the upper right. Select 'New Dashboard'
3. Click the blue button saying '+ Add visualization'
4. A window pops up, titled 'Select data source'. Click on 'biomed' with the green 'default'-mark in the list.

A blank visualization appears with control elements for data queries below. Follow these steps to query the database for your temperature data:
1. 



## Delete unused Data
Click 'Manage Data' on the website menu bar
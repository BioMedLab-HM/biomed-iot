# Biomed IoT - User Manual

This is the Biomed IoT User Manual. The installation instructions for Admins can be found in the [README document (ext. link)](README.md).  

*About Biomed IoT*
Biomed IoT is an open source IoT platform for data acquisition, visualization and automation. It enables the integration and real-time analysis of sensors and effector devices. It is optimized for data security and privacy, making it suitable for medical data, such as in clinical trials.

*About this Manual*
This manual explains how to use the Biomed IoT platform with a simple application example. You will learn how to:
- Send temperature and humidity data from an ESP32 microcontroller with a DHT 22 sensor to an MQTT topic on the platform
- Setup and learn about the Biomed IoT Gateway (if Biomed IoT is running on an internet server)
- Store this data in the database using Node-RED&reg;
- Use Node-RED for automation
- Visualize the data in Grafana
- Delete or export data as CSV file for download

First have a look at the [schematic presentation of Biomed IoT in the README document](README.md#how-it-works). You will see how sensors, an optional gateway and the platform are linked together. Then come back to this user manual.

## Table of Content

- [Registration and Login](#registration-and-login)
- [Link Device to the Platform](#link-device-to-the-platform)
    - [Variant 1: With Gateway (use this if Biomed IoT is accessable on the internet)](#variant-1-with-gateway)
    - [Variant 2: Without Gateway](#variant-2-without-gateway)
- [Create Automations and Save Data With Node-RED](#create-automations-and-save-data-with-node-red)
- [Visualize with Grafana&reg;](#visualize-with-grafana)
- [Delete or Export Data as CSV file](#delete-or-export-data-as-csv-file)
- [Alternatively: Export a CSV File with Grafana](#alternatively-export-a-csv-file-with-grafana)

## Registration and Login

1. Click on 'User' and then on 'Register' on the website menu bar.
2. Fill the form with all necessary data. The password needs to comply with the rules for safe passwords, listed there.
3. If email validation is active (e.g. when Biomed IoT runs on the internet) you will receive an email with a verification link. In this case you need to click this link before you can log in with your email and password.

[(Back to Table of Contents)](#table-of-content)

## Link Device to the platform

Data can be sent to the platform directly (recommended when the platform is running on a server in your local network)
or indirectly by sending data to a local Biomed IoT gateway (e.g. a Raspberry Pi) that forwards the message to the platform with encryption (recommended if the Biomed IoT platform is running on an internet server)

### Variant 1: With Gateway 

*e.g. when Biomed IoT is running on the internet where TLS encryption (https) is needed*
1. Go to 'Gateway Setup' page and follow the instructions there to create MQTT credentials for your gateway. For example use "gateway_01" as device name.
2. Go to the 'Code Examples' page, copy the 'ESP32 + DHT22 Sensor (for use with gateway)' and use it for your ESP32+DHT22 setup. You will find further instructions for code adjustment and hardware setup in the code.
3. When you have finished the code and hardware setup, start your ESP32. It will already send data to the gateway. To actually receive and save the data on the platform follow the instructions for Node-RED below.

### Variant 2: Without Gateway

*when Biomed IoT is running in a secure local network where no TLS encryption (https) is needed*
1. Create device credentials for your ESP32 on the 'Device List' page. For example use "esp32_01" as device name.
2. Get your personal topic ID from the 'Message & Topic Structure' page.
3. Go to the 'Code Examples' page, copy the 'ESP32 + DHT22 Sensor (for use without gateway)' and use it for your ESP32+DHT22 setup. You will find further instructions for code adjustment and hardware setup in the code (device credentials and personal topic ID needed)
4. When you finished the code and hardware setup, start your ESP32. It will already send data. To actually receive and safe the data on the platform follow the instructions for Node-RED below.

[(Back to Table of Contents)](#table-of-content)

## Create Automations and Save Data with Node-RED

1. Click 'Automate' on the website menu and follow the instructions there.
2. After Node-RED startup process is finished you will be on the page, saying 'Your Node-RED is running'. Open the Nod-RED Flow Editor (left dark blue button).
2. Once you have opened the Node-RED Flow Editor, you need to adjust one value in the 'Prepare Data for Database'-function node of the subflow for the esp32 temperature values (the middle one of the three). Double click the function node and replace 'yourMeasurementNameHere' by a broad and short name for your measurement: for example if you measure temperature and other values of a fridge in the lab, use 'labfridge'. You can also use your devicename which you defined on the "Device list" page (e.g. 'esp32_01' which would be more generic compared to 'labfridge'). The measurement name you choose will affect how your data is saved to the InfluxDB&reg; time series database.
3. Finally click on the red deploy button in the top right corner of the flow editor to apply your changes. Your temperature data is now saved to the database. If you want humidity to be saved too, copy the '...esp32/temperature' mqtt in node and place it right above the other one, double click it and change the subtopic 'temperature' to 'humidity'. Click on the red button 'Fertig' or 'Done'. Then wire the new mqtt in node with the existing function node for your 'labfridge' or 'esp32_01' (whichever you choosed) measurement by clicking on its small gray end and draw the wire to the function node left end. Click the red deploy button again. Now your humidity data will also be saved to the database.  
4. Optional: The MQTT-Out nodes on the right side of the example flow show the topics you can subscribe to in order to receive a code 0 or 1. These codes depend on the temperature thresholds set in the function nodes before each "mqtt out" node in the cputemp or dht22-temperature subflows. (A subscriber script is not included in this version of the manual.)

[(Back to Table of Contents)](#table-of-content)

## Visualize with Grafana

Click on 'Visualize' on the website menu.
First create a new dashboard and add a visualization:
1. Click on 'Dashboards' (menu on the left)
2. Click the blue button saying 'New' on the upper right. Then select 'New Dashboard'
3. Click the blue button saying '+ Add visualization'
4. A window pops up, titled 'Select data source'. Click on 'biomed' with the green 'default'-mark in the list. Or just close the pop-up with the 'x' on the top right.

A blank visualization with control elements for data queries below appears. Follow these steps to query the database for your temperature data (ignore the red warning symbol on the visualizations area upper left corner for now):  
Below the blank visualization is a form field to make queries to the database.
1. In the line that says 'FROM' click 'select measurement'. Choose 'devicestatus'.
2. In the field that says 'SELECT' click on field(value). Choose your devicename (either the gateway name or ESP32 name you chose on the "Device List" page) from the dropdown or enter it manually
3. Above the visualization area, select 'Last 5 minutes' (next to the clock symbol) to show the last five minutes of data and click the refresh icon (two circular arrows)
4. In the Panel options (on the right) set the Title to 'Device Status'
5. Click on the blue 'Save dashboard' button (top right corner) and confirm the pop-up with "Save"
6. Click on the "Back to dashboard" button in the Grafana menu bar right above your dashboard (a menu slides in from the right).

- Now you should see your device status visualization on your dashboard.
- Adjust the time range or the panel size to your needs.
- You may also want to activate auto refresh: Click on the small down facing arrow next to the refresh icon and select for example 5s (seconds). Your diagram will update every 5 seconds
- It is possible to add other device's status to the diagram. 
- For more information follow the [Grafana docs](https://grafana.com/tutorials/).

If you want to visualize your temperature or humidity data from your ESP32 or CPU temperature from your gateway (if you have set up one), click on 'Add' in the Grafana menu icon bar (you may click the 'Edit' Button first) and select 'Visualization'. Repeat the process above to configure your Visualization. For measurement name use 'esp32_01' (or whichever you used in Node-RED) and for 'field(value)' select 'temperature' or 'humidity' respectively.

[(Back to Table of Contents)](#table-of-content)

## Delete or Export Data as CSV file

Click on 'Manage Data' on the website menu.
1. Select the measurement you want to delete. Let's select 'devicestatus' for now.
2. Click the 'Download CSV' button. A MS Excel compatible csv file will be downloaded.
3. Click the 'Delete Data' button and confirm. All your 'devicestatus' data is now deleted and your Visualization in Grafana should be showing no data points. After a minute or less though, there will be new status data coming from your device.

- You can set a specific time range and select only certain data fields of your measurement. The field itself will not be deleted, only the stored values.

[(Back to Table of Contents)](#table-of-content)

## Alternatively: Export a csv file with Grafana 
Note: actual process might be slightly different with future updates of Grafana
Note: This procedure only shows and exports data points that are querried from InfluxDB by grafana. If you use mean() in your SELECT statement and/or time interval in GROUP BY not all data points will be querried. By this, Grafana saves ressources.

1. Select a time range for your data (as you did before, see Grafana menu bar) that includes the part you want to export
2. Hover over your visualization with your mouse
3. On its upper right corner click on the three small black dots, then on 'Inspect' and then on 'Data'
4. You can see a table of your data with timestamps and values, else click 'Data options' and make sure your field name (e.g. 'esp32' or your gateway's name) is selected
5. In 'Data options' you can also check 'Download for Excel' to get the right format for MS Excel&reg;.
6. Click 'Download CSV' and check your computer's download folder.
  
  
## 
This concludes the manual.

[(Back to Table of Contents)](#table-of-content)

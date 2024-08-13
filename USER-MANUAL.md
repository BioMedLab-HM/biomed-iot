# Biomed IoT - User Manual

This is the Biomed IoT User Manual. The installation instructions can be found in the [README file](README.md).  
The manual will be expanded in the future to explain additional features of the platform.

This manual explains how to use the Biomed IoT platform with a simple application example. You will learn how to:
- Send temperature and humidity data from an ESP32 microcontroller with a DHT 22 sensor to the platform
- Setup and learn about a Biomed IoT Gateway (if Biomed IoT is running on an internet server)
- Store this data in the database using Node-RED
- Use Node-RED for automation
- Visualize the data in Grafana
- Export the data from Grafana as a CSV file for download
- Delete the data from the database again

First have a look at the [schematic presentation of Biomed IoT](README.md#how-it-works). You will see how sensors, an optional gateway and the platform are linked together. Then come back to this user manual.

## Content
- [Registration and Login](#registration-and-login)
- [Link Device to the Platform](#link-device-to-the-platform)
    - [Variant 1: With Gateway (use this if Biomed IoT is accessable on the internet)](#variant-1-with-gateway)
    - [Variant 2: Without Gateway](#variant-2-without-gateway)
- [Create Automations and Save Data With Node-RED](#create-automations-and-save-data-with-node-red)
- [Visualize with Grafana](#visualize-with-grafana)
- [Export a CSV File with Grafana](#export-a-csv-file-with-grafana)
- [Delete Data](#delete-data)

## Registration and Login
1. Click on 'User' and then on 'Register' on the website menu bar.
2. Fill the form with all necessary data. The password needs to comply with the rules for safe passwords, listed there.
3. If email validation is active (e.g. when Biomed IoT runs on the internet) you will receive an email with a verification link. In this case you need to click this link before you can log in with your email and password.

## Link Device to the platform
Data can be sent to the platform directly (recommended when the platform is running on a server in your local network)
or indirectly by sending data to a local Biomed IoT gateway that forwards the message to the platform with encryption (recommended if the Biomed IoT platform is running on an internet server)

### Variant 1: With Gateway 
*e.g. when Biomed IoT is running on the internet where TLS encryption (https) is needed*
1. Go to 'Gateway Setup' page and follow the instructions there.
2. Go to the 'Code Examples' page, copy the 'ESP32 + DHT22 Sensor (for use with gateway)' and use it for your ESP32+DHT22 setup. You will find further instructions for code adjustment and hardware setup in the code.
3. When you finished the code and hardware setup, start your ESP32. It will already send data. To actually receive and save the data on the platform follow the instructions for Node-RED below.

### Variant 2: Without Gateway
*when Biomed IoT is running in a secure local network where no TLS encryption (https) is needed*
1. Create device credentials for your ESP32 on the 'Device List' page
2. Get your personal topic ID from the 'Message & Topic Structure' page.
3. Go to the 'Code Examples' page, copy the 'ESP32 + DHT22 Sensor (for use without gateway)' and use it for your ESP32+DHT22 setup. You will find further instructions for code adjustment and hardware setup in the code (device credentials and personal topic ID needed)
4. When you finished the code and hardware setup, start your ESP32. It will already send data. To actually receive and safe the data on the platform follow the instructions for Node-RED below.

## Create Automations and Save Data With Node-RED
1. Click 'Automate' and then on 'Open here' or 'Open in new tab' (more convenient) on the website menu and follow the instructions there.
2. Once you opened the Node-RED Flow Editor and made the described modifications to the nodes according to the instructions before, your temperature and humidity data is saved to the database. The MQTT-Out nodes on the right side show the topics where you can subscribe to get a Code 0 or 1 depending on the temperature threshold in the subflows for cputemp or dht22-temperature (a subscriber script is not provided in this version of the manual).

## Visualize with Grafana
Click on 'Visualize' on the website menu.
First create a new dashboard and add a visualization
1. Click on 'Dashboards' (menu on the left)
2. Click the blue button saying 'New' on the upper right. Select 'New Dashboard'
3. Click the blue button saying '+ Add visualization'
4. A window pops up, titled 'Select data source'. Click on 'biomed' with the green 'default'-mark in the list.

A blank visualization appears with control elements for data queries below. Follow these steps to query the database for your temperature data (ignore the red warning symbol on the visualizations area upper left corner for now):  
Below the blank visualization is a form field to make queries to the database. Now, let's query for your device status data.
1. In the line that says 'FROM' click 'select measurement'. Choose 'devicestatus' or enter it manually
2. In the field that says 'SELECT' click on field(value). Choose your devicename from the dropdown or enter it manually
3. Above the visualization area, select 'Last 5 minutes' (next to the clock symbol) to show the last five minutes of data and click the refresh icon (two circular arrows)
4. In the Panel options (on the right) set the Title to 'Device Status'
5. Click on the blue 'Apply' button (top right corner)
6. Click on the small gray diskette symbol in the Grafana menu icon bar right above your dashboard (a menu slides in from the right), set the Title to 'Device Status' and click on the blue 'Save' button.

- Now you should see your device status visualization on your dashboard.
- Adjust the time range to your needs. 
- You may also want to activate auto refresh: Click on the small down facing arrow next to the refresh icon and select for example 5s (seconds). Your diagram will update every 5 seconds
- It is possible to add other device's status to the diagram, but this will be explained in a later, more comprehensive version of the manual

If you want to visualize your temperature data from your ESP32 or CPU temperature from your gateway (if you have set up one), click on 'Add' in the Grafana menu icon bar and select 'Visualization'. Repeat the process above to configure your Visualization. For measurement name use 'esp32' (as was already set in Node-RED) and for 'field(value)' select 'temperature'.

## Export a csv file with Grafana
1. Select a time range for your data (as you did before, see Grafana menu bar) that includes the part you want to export
2. Hover over your visualization with your mouse
3. On its upper right corner click on the three small black dots, then on 'Inspect' and then on 'Data'
4. You can see a table of your data with timestamps and values, else click 'Data options' and make sure your field name (e.g. 'esp32' or your gateway's name) is selected
5. In 'Data options' you can also check 'Download for Excel' to get the right format for MS Excel&reg;.
6. Click 'Download CSV' and check your computer's download folder.

## Delete Data
1. Click 'Delete Data' on the website menu bar and read the instructions there
2. select 'devicename' in the 'Select Measurement' field, click on the 'Delete Data' button and confirm with 'OK'

All your 'devicestatus' data is now deleted and your Visualization in Grafana should be showing no data points.  
Don't worry, after a minute or less there will be new status data coming from your device.

This concludes the manual.

[(Go Back to Table of Contents)](#content)

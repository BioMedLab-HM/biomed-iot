# Biomed IoT

Biomed IoT is an open source IoT platform for data acquisition, visualization and automation. It enables the integration and real-time analysis of sensors and effector devices. It is optimized for data security and privacy, making it suitable for medical data, such as in clinical trials. It is built on the Django&reg; framework and provides its core functionality by integrating the Eclipse Mosquitto™ MQTT broker, Node-RED&reg;, InfluxDB&reg; and Grafana&reg;.

## Content

- [How it works](#how-it-works)
- [Installation](#installation)
    - [Requirements](#requirements)
    - [Setup](#setup)
    - [Troubleshooting](#troubleshooting)
- [Performance Testing](#performance-testing)
- [How to use](#how-to-use)


## How it Works

The figure below explains the functionality of Biomed IoT on a high level
- Sensors can send data to the Biomed IoT platform (server) via the MQTT protocol as MQTT messages to an MQTT topic (or over a gateway if the platform is running online).
- An MQTT topic is like a label that tells devices where to send or get the messages
- On the website, the user can store data to a database, create visualizations and send data out to effector devices
- If you already have access to a ready set up Biomed IoT, go to section [How to use](#how-to-use)
- Get a deeper understanding for the concept and implementation of Biomed IoT, by consulting the underlying master's thesis [here](https://www.researchgate.net/publication/384329057_Weiterentwicklung_einer_Open_Source_IoT-Plattform_fur_Laborautomatisierung_mit_containerbasierten_Node-RED-Instanzen_fur_mehrere_Nutzer) or [here](https://opus4.kobv.de/opus4-hm/frontdoor/index/index/docId/727).

![Biomed IoT Schema](biomed_iot/media/biomed_iot.png "Biomed IoT Schema")


## Installation

### Requirements

The setup and platform have been tested on a cleanly installed Debian 12 server (x86 and ARM) and under Raspberry Pi OS (64-Bit) on a Raspberry Pi 4, both running Python 3.11.2. It is recommended that you create a new Linux user (included in the sudo group) under which the platform will run (instructions see below).  
To enable email verification for platform users, an SMTP email provider with 'App-password' is necessary. For example, Gmail&reg; offers this for free. during the Biomed IoT installation process you will be asked for the SMTP email server, port, email address and App-password.

### Setup

If you want to set up Biomed IoT server on a Raspberry Pi, you can use [Debian for Pi](https://raspi.debian.net) or, the easier way, [Raspberry Pi OS light (64 Bit)](https://www.raspberrypi.com/software/operating-systems/), flashed to an SD-card using the [Raspberry Pi Imager](https://www.raspberrypi.com/software/). If you are using Raspberry Pi OS, the user can be created before the flashing process with the Raspberry Pi Imager. In this case you can omit the first steps and start with ‘Add your newly created user to the sudo group‘.

First prepare your system for the Biomed IoT setup. Read and understand the instructions carefully before executing the following commands:


Switch to user 'root' and enter the password when prompted
```
su -
```
Create a new user if you have not already done so with the command below (choose your own name for <your-username>) and follow the instructions (entries for 'Full name', 'Room number' etc. are not necessary):
```
adduser <your-username>
```
Install the 'sudo' command capability (if not yet installed). This will later allow your user to temporarily perform a command with elevated (root) privileges
```
apt install sudo
```
Add your newly created user to the sudo group
```
usermod -G sudo <your-username>
```
To use 'sudo' with the new user without being prompted for your password, execute
```
visudo
```
A file opens in the editor (e.g. nano). Append this line to the end of the file:
```
<your-username> ALL=(ALL) NOPASSWD: ALL
```
Now switch to your new user:
```
su <your-username>
```

Make sure your system is up to date by executing
```
sudo apt update
sudo apt -y full-upgrade
```
Install the following packages:
```
sudo apt -y install net-tools git python3-pip python3-venv
``` 
Then reboot the system
```
sudo reboot
```

The guided installation process will ensure that Biomed IoT is installed on your system.
Login to your Linux terminal with your new user.
Clone the repository and start the Biomed IoT installation by executing the following commands
```
cd ~
git clone https://github.com/BioMedLab-HM/biomed-iot.git
cd biomed-iot
sudo python3 setup.py
```
Read the last lines at the end of the installation (e.g. for the URL or IP address to reach Biomed IoT in the web browser or where to find the login password for the admin account for which you already provided an email address during the setup process), then reboot, to make the Biomed IoT Platform fully work:
``` 
sudo reboot
```

The Biomed IoT should now be up and running. Type your server's IP address or domain in a web browser.  

### First Login
To log in to the Biomed IoT platform as admin, go to the Login page and use the email address you provided during setup. The password was auto-generated. Execute the following command in the servers terminal to print it to the terminal:
```
grep DJANGO_ADMIN_PASS /etc/biomed-iot/config.toml | cut -d '"' -f2
```

### The config.toml file
Contains important settings for the project. These are read dynamically during operation (when the server starts). With few exceptions, these parameters must not simply be changed.

Parameters that can be safely changed during operation (changes take effect after restarting the Gunicorn server with sudo systemctl restart gunicorn):

- **All parameters under [mail]**: Sets the login credentials for the SMTP email access used for email validation and password reset. Includes EMAIL_VERIFICATION: 'true' or 'false' ('true' triggers email verification emails to be sent; requires SMTP email credentials).
- **INOUT_TOPIC_ENABLED**: ('true' shows a checkbox on the 'Device List' page. If checked when creating MQTT credentials, it allows publishing and subscribing to subtopics under inout/<USER_TOPIC_ID>/ (useful for connecting, e.g., Shelly&reg; plugs directly to the platform)).
- **DJANGO_DEBUG**: 'true' or 'false' ('true' displays Python error messages in the browser → not intended for production systems).
- **TIME_ZONE**: Warning: Changing during operation has not yet been tested. Sets the time zone. Relevant for CSV data export.
- **REGISTRATION_ENABLED**: 'false' hides the user registration page → protection against spam sign-ups.

*If you must edit this file for some reason, use sudo. Do not change any value in this file except you know exactly what you are doing.*

### Troubleshooting

- Do not abort the setup process prematurely. Depending on the speed of the download servers, the duration of the setup can vary, usually between 2 and 10 minutes.
- The setup script requires root privileges. Ensure that the setup command was executed with sudo like written in the setup description above.
- The safest way to repeat the installation of Biomed IoT is to re-setup your operating system from scratch (e.g. flashing the SD of for your Pi).
- Execute the [*Tests After Installation*](tests/tests_after_setup.md) to check the integrity of your installation.

## Performance Testing

The script ~/biomed-iot/tests/mqtt_load_tests/sine_load_test.py sends high frequency data to the platform for. Follow the instructions in the file.

## How to Use

The [*user manual*](USER-MANUAL.md) (see also 'Manual' in the website menu) contains a guided tour through Biomed IoT and helps you to set up a working example.

Use the platform at your own risk. If you serve it on a public server, use a legitimate privacy policy and imprint. 

[(Go Back to top)](#biomed-iot)
#
Have fun using Biomed IoT!  

René Sesgör ([GitHub](https://github.com/AwakeAndReady))

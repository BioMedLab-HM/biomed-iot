# Tests After Installation

[(Back to the README file)](../README.md)  

### Reboot if not yet done
	sudo reboot

### Check config.toml and get DJANGO_ADMIN_PASS for website login
	nano /etc/biomed-iot/config.toml

### Website
Check all functions (at least check if each page and service like Node-RED and Grafana opens)
Check Database by using an MQTT-in node in Node-RED and send {"test":1} to the topic for devicestatus. Then delete the data.

### Website Admin Dashboard
Go to the '/admin' path of the website
for credentials, (see DJANGO_ADMIN_PASS in config.toml)
Check for completeness of data for:
- Profile (Email)
- Node red user datas (will be created only after first start of Node-RED)
- Mqtt meta datas (User Topic ID, Nodered Role Name, Device Role Name)
- Mqtt clients (Username, Password, Textname, Rolename)
- Influx user datas (Bucket Name, Bucket ID, Bucket Token)

### Setup Logs
	cd /home/<user>/biomed-iot/setup_files/setup_logs  # substitute <user> with your linux username
	ls -al
	grep -R "Error" .  # search for "Error" or other keywords in log files
	# Read all setup logs
	nano main.log
	nano install_xx_<name>.log  # substitute 'xx_<name>' according to the respective log file name

### Nginx
	sudo nginx -t
	sudo systemctl status nginx.service

### Gunicorn
	sudo systemctl status gunicorn.socket
	sudo systemctl status gunicorn.service
	journalctl -u gunicorn.service -n -f  # auch während Webseitentest

### Docker/Node-RED
	docker ps -a  # list all containers

### Mosquitto und Mosquitto dynamic-security.json
	sudo systemctl status mosquitto.service
	sudo nano /var/lib/mosquitto/dynamic-security.json

### PostgreSQL (with <your_postgres_user> from config.toml)
	sudo systemctl status postgresql
	sudo -u postgres psql -U postgres  # login to postgres CLI as postgres admin
	\du  # list all users with their roles
	\l  # list all databases
	\dt  # List database tables
	exit  # to exit psql CLI

### Optional:
Check files in 
```
~/biomed-iot/setup_files/tmp
```
Have all variables been inserted correctly?

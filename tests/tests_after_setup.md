# Tests After Installation

[(Back to the README file)](../README.md)  

### Reboot if not yet done
	sudo reboot

### Check config.toml and get DJANGO_ADMIN_PASS for website login
	nano /etc/biomed-iot/config.toml

### Website
Check all functions

### Website Admin Dashboard
\<ip>/admin or \<domain>/admin  
for credentials, see DJANGO_ADMIN_PASS in config.toml

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

### Setup Logs
	cd /home/<user>/biomed-iot/setup_files/setup_logs
	ls -al
	grep -R "Error" .  # search for "Error" or other keywords in log files
	nano main.log
	nano install_xx_<name>.log

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

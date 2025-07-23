# Secure NGINX + Let’s Encrypt TLS Setup
_**This manual setup has been integrated into the automated setup of Biomed IoT. It is just kept for reference**_

This guide walks you—step by step—through hardening an NGINX server with a free Let’s Encrypt certificate.  
Everything is done from a **terminal** with **sudo** rights.

---
> **Important:** copy-and-paste the commands and just replace `example.com` with your real domain.
---

## 2 · Step-by-step commands

> **Run each command as shown (they’re all `sudo`).**  
> Lines that wrap are still one command.

### 2.0 Add ufw rule for TLS (if not already existing)
```bash
sudo ufw allow 443/tcp
```
### 2.1  Update APT & install required packages
```bash
sudo apt update
sudo apt install -y openssl certbot python3-certbot-nginx
```
### 2.2 Generate a domain-specific NGINX vhost from the template
```bash
mkdir ~/biomed-iot/setup_files/tmp
sudo bash ~/biomed-iot/setup_files/config/tmp.nginx-biomed-iot-tls-domain.conf.sh example.com \
     > ~/biomed-iot/setup_files/tmp/nginx-biomed-iot-tls-domain.conf
```
### 2.3 Move the http vhost into place & enable it (check for other links in sites-enabled and delete if necessary)
```bash
sudo cp ~/biomed-iot/setup_files/tmp/nginx-biomed-iot-tls-domain.conf \
        /etc/nginx/sites-available/example.com.conf
sudo cp /etc/nginx/sites-available/example.com.conf \
        /etc/nginx/sites-available/example.com.http.conf
# Delete the 443 server block in the ...http.conf file
sudo ln -s /etc/nginx/sites-available/example.com.http.conf /etc/nginx/sites-enabled
# Test and reload 
sudo nginx -t
sudo systemctl reload nginx
```
### 2.4 Create a strong Diffie–Hellman parameter file (one-off, ~1 min)
```bash
sudo openssl dhparam -out /etc/nginx/dhparam.pem 2048 # or 3072
```
### Create Let's Encrypt deploy hook for nginx
Create directory and file
```bash
sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy
sudo nano /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```
Write the following lines into the file and save it:
```bash
#!/bin/bash
systemctl reload nginx
```
Then make it executable:
```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```
### 2.5 Request & install a Let’s Encrypt certificate (use your own domain name)
1) Create the full webroot path (including the acme-challenge subfolder):
```bash
sudo mkdir -p /var/www/letsencrypt/.well-known/acme-challenge
```
2) Change owner and group to match your 'static' directory (owner=<your-linux-user>, group=www-data):
```bash
sudo chown -R <your-linux-user>:www-data /var/www/letsencrypt
```
3) Set permissions to 2775 (for all subfolders):
```bash
sudo chmod -R 2775 /var/www/letsencrypt
```
Then run certbot (replace example.com with your own domain) and enable the new https server block
```bash
sudo certbot certonly --webroot -w /var/www/letsencrypt -d example.com -d www.example.com
sudo ln -s /etc/nginx/sites-available/example.com.conf /etc/nginx/sites-enabled
```
Follow the interactive prompts. Certbot will:

Prove domain ownership via HTTP-01 challenge.
Edit the NGINX vhost so HTTPS traffic is redirected.

### 2.6 Install the recommended SSL parameters snippet if not yet existing
```bash
sudo cp ~/biomed-iot/setup_files/config/tmp.ssl-params.conf \
        /etc/nginx/snippets/ssl-params.conf
```
### 2.7 Enable the TLS-Passthrough stream module for MQTT
```bash
sudo bash ~/biomed-iot/setup_files/config/tmp.nginx-stream-tls-domain.conf.sh example.com \
     > ~/biomed-iot/setup_files/tmp/tmp.nginx-stream-tls-domain.conf

sudo cp ~/biomed-iot/setup_files/tmp/tmp.nginx-stream-tls-domain.conf \
        /etc/nginx/modules-available/nginx-stream-tls-domain.conf

sudo ln -s /etc/nginx/modules-available/nginx-stream-tls-domain.conf \
           /etc/nginx/modules-enabled
```

### 2.8 Check syntax & reload NGINX
```bash
sudo nginx -t
```
If you see syntax is ok reload nginx
```bash
sudo systemctl reload nginx
```

If test is successful, your site is now live on HTTPS at your specified domain name.

## 3 · Automatic certificate renewal
Certbot installs a systemd timer that renews certificates twice daily and reloads NGINX only if a renewal happens. Verify with:
```bash
systemctl list-timers | grep certbot
```

## 4 · Update Gateway Setup zip File

### 4.1 Create a temporary work directory
```bash
mkdir ~/build_gateway_zip
cd ~/build_gateway_zip
```
### 4.3 Copy the two scripts into your temp directory
```
cp ~/biomed-iot/setup_files/config/gateway_setup.sh ./
cp ~/biomed-iot/setup_files/config/publish_cpu_temp.sh ./
```
### 4.4 Edit gateway_setup.sh to update the bridge_cafile line
```
nano gateway_setup.sh
```
Change the code according to the comments about Let's Encrypt (ISRG_Root_X1.pem) and self-signed cert (biomed-iot.crt).

Then save and exit


### 4.6 Create the ZIP archive
Create the ZIP archive
```
zip biomed_iot_gateway.zip  gateway_setup.sh \
                            publish_cpu_temp.sh
```
### 4.7 Move the ZIP into the public download folder
```
sudo mv biomed_iot_gateway.zip /var/www/biomed-iot/media/public_download_files/
```
### 4.8 Clean up the temporary directory
```
cd ~
rm -rf ~/build_gateway_zip
```
Back to [*README.md*](README.md)

[(Go Back to top)](#secure-nginx--lets-encrypt-tls-setup)

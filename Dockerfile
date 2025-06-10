# Build command (if changes are made to settings.js after platform setup): 
# docker build -t custom-node-red .

# Use the official Node-RED base image
FROM nodered/node-red:latest

# Set the user to root to allow npm install and other operations
USER root

# Install additional Node-RED nodes
RUN npm install node-red-dashboard node-red-contrib-influxdb jsonwebtoken

# Remove specific nodes by deleting their files
#function
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/function/90-exec.html
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/function/90-exec.js
# network
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/network/06-httpproxy.html
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/network/06-httpproxy.js
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/network/21-httpin.html
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/network/21-httpin.js
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/network/21-httprequest.html
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/network/21-httprequest.js
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/network/22-websocket.html
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/network/22-websocket.js
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/network/31-tcpin.html
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/network/31-tcpin.js
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/network/32-udp.html
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/network/32-udp.js
# storage
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/storage/10-file.html
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/storage/10-file.js
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/storage/23-watch.html
RUN rm -f /usr/src/node-red/node_modules/@node-red/nodes/core/storage/23-watch.js

# Copy templated flows.json into the default /data folder of the image
COPY biomed_iot/users/services/nodered_flows/flows.template.json /data/flows.json

# use custom settings.js for authentication
COPY setup_files/config/settings.js /data/settings.js

# Set the ownership of the files to the node-red user
RUN chown -R node-red:node-red /data

# Expose port 1880 for external access
EXPOSE 1880

# Set user back to node-red for security best practices
USER node-red

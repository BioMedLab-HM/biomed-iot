# Build command: docker build -t custom-node-red .

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

# use custom settings.js for authentication
# COPY settings.js /data/settings.js
# COPY auth-middleware.js /data/auth-middleware.js

# Set the ownership of the files to the node-red user
RUN chown -R node-red:node-red /data

# Expose port 1880 for external access
EXPOSE 1880

# Set user back to node-red for security best practices
USER node-red

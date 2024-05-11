# Use the official Node-RED base image
FROM nodered/node-red:latest

# Set the user to root to allow npm install and other operations
USER root

# Install additional Node-RED nodes
RUN npm install node-red-dashboard node-red-contrib-influxdb

# TODO: copy custom settings.js for authentication logic
# COPY settings.js /data/settings.js

# Expose port 1880 for external access
EXPOSE 1880

# Set user back to node-red for security best practices
USER node-red

#!/bin/bash

# Run the Docker container
sudo docker run -p 8888:8888 --name graipe webodmapi

# Clone the WebODM repository
git clone https://github.com/OpenDroneMap/WebODM --config core.autocrlf=input --depth 1

# Navigate into the WebODM directory
cd WebODM

# Start the WebODM server
./webodm.sh start
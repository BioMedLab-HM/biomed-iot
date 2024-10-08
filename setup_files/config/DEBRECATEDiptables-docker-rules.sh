#!/bin/bash

# Block inter-container communication on docker0, but allow traffic to and from 172.17.0.1 (the host)
iptables -I DOCKER-USER -i docker0 ! -d 172.17.0.1 -o docker0 -j DROP
iptables -I DOCKER-USER -i docker0 -s 172.17.0.1 -o docker0 -j ACCEPT

#!/bin/bash

# Script to connect to a router's bgpd shell.

# router will be the first argument or if there is no arguments it will be "R1"
router=${1:-R1}

echo "Connecting to $router shell"

sudo python run.py --node $router --cmd "telnet localhost bgpd"

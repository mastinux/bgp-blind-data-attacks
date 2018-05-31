#!/bin/bash

node="atk1"
bold=`tput bold`
normal=`tput sgr0`

sudo python run.py --node $node --cmd "ping -c 3 9.0.0.1"
sudo python run.py --node $node --cmd "ping -c 3 9.0.0.2"

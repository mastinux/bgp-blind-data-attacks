#!/bin/bash

node="atk1"
bold=`tput bold`
normal=`tput sgr0`

sudo python run.py --node $node --cmd "tcpdump -i atk1-eth0 -ln 'not arp'"

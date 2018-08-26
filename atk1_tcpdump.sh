#!/bin/bash

node="atk1"
bold=`tput bold`
normal=`tput sgr0`

sudo python run.py --node $node --cmd "tcpdump -i atk1-eth0 -lnSe"

#sudo python run.py --node $node --cmd "tcpdump -i atk1-eth0 \"host 9.0.0.1 or host 9.0.0.2\""

#sudo python run.py --node $node --cmd "tcpdump -i atk1-eth0 \"src port 179\" or \"dst port 179\""

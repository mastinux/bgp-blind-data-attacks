#!/bin/bash

node="testhost1"
bold=`tput bold`
normal=`tput sgr0`

#sudo python run.py --node $node --cmd "tcpdump -i testhost1-eth0 -ln 'not arp'"

#sudo python run.py --node $node --cmd "tcpdump -i testhost1-eth0 -lnSe 'dst host 9.0.1.1'"

sudo python run.py --node $node --cmd "tcpdump -i testhost1-eth0 -w /tmp/testhost1_tcpdump.cap"

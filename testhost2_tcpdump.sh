#!/bin/bash

node="testhost2"
bold=`tput bold`
normal=`tput sgr0`

sudo python run.py --node $node --cmd "tcpdump -i testhost2-eth0 -ln 'not arp'"

# sudo python run.py --node $node --cmd "tcpdump -i testhost2-eth0 -ln 'not arp' -w /tmp/testhost2_tcpdump"

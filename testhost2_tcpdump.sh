#!/bin/bash

node="testhost2"
bold=`tput bold`
normal=`tput sgr0`

# sudo python run.py --node $node --cmd "tcpdump -i testhost2-eth0 -lnS 'not arp and src host 9.0.1.2 and dst host 9.0.1.1'"

#sudo python run.py --node $node --cmd "tcpdump -i testhost2-eth0 -ln 'tcp[tcpflags] & (tcp-rst) != 0'"

sudo python run.py --node $node --cmd "tcpdump -i testhost2-eth0 -w /tmp/testhost2_tcpdump.cap"

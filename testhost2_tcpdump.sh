#!/bin/bash

node="testhost2"
bold=`tput bold`
normal=`tput sgr0`

sudo python run.py --node $node --cmd "tcpdump -i testhost2-eth0 -lnS 'not arp and src host 9.0.1.2 and dst host 9.0.1.1'"

#echo 'FILTERING RST PACKETS'
#sudo python run.py --node $node --cmd "tcpdump -i testhost2-eth0 -ln 'tcp[tcpflags] & (tcp-rst) != 0'"

# sudo python run.py --node $node --cmd "tcpdump -i testhost2-eth0 -ln 'not arp' -w /tmp/testhost2_tcpdump"

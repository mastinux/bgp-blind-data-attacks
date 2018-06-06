#!/bin/bash

node="testhost2"
bold=`tput bold`
normal=`tput sgr0`

sudo python run.py --node $node --cmd "tcpdump -i testhost2-eth0 -l"

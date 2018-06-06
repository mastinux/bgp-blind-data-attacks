#!/bin/bash

node="testhost1"
bold=`tput bold`
normal=`tput sgr0`

sudo python run.py --node $node --cmd "tcpdump -i testhost1-eth0 -l"

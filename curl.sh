#!/bin/bash

snode=${1:-h1-1}
dnode=${2:-h2-1}
bold=`tput bold`
normal=`tput sgr0`

while true; do
    out=`sudo python run.py --snode $snode --dnode $dnode --cmd "curl -s"`
    date=`date`
    echo $date -- $bold$out$normal
    sleep 3
done

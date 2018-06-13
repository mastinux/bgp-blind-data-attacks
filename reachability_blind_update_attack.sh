#!/bin/bash

node="h1-2"

while true; do
	#echo "-----------------------------------------------------------"
    out=`sudo python run.py --node $node --cmd "ping -c 1 15.0.0.1"`
	#echo "$out"
	myline=`echo "$out" | head -2` # selecting first two lines

	if [ ${#myline} -eq 0 ]; then
		myline=`echo "$out" | head -2`
	fi

	#echo "-----------------------------------------------------------"
	echo "$myline"
	echo
	#echo ">>> ${#myline}"
	
    sleep 3
	#echo "-----------------------------------------------------------"
done

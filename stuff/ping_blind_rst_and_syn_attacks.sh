#!/bin/bash

lxterminal -e "/bin/bash -c 'echo \"origin h1-2 destination h3-1\"; sudo python ./run.py --snode h1-2 --dnode h3-1 --cmd ping'" &
lxterminal -e "/bin/bash -c 'echo \"origin h1-2 destination h4-1\"; sudo python ./run.py --snode h1-2 --dnode h4-1 --cmd ping'" &

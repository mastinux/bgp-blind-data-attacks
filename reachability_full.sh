#!/bin/bash

lxterminal -e "/bin/bash -c 'echo \"origin h1-2 destination h1-1\"; /home/mininet/bgp-blind-data-attacks/curl.sh h1-2 h1-1'" &
lxterminal -e "/bin/bash -c 'echo \"origin h1-2 destination h2-1\"; /home/mininet/bgp-blind-data-attacks/curl.sh h1-2 h2-1'" &
lxterminal -e "/bin/bash -c 'echo \"origin h1-2 destination h3-1\"; /home/mininet/bgp-blind-data-attacks/curl.sh h1-2 h3-1'" &
lxterminal -e "/bin/bash -c 'echo \"origin h1-2 destination h4-1\"; /home/mininet/bgp-blind-data-attacks/curl.sh h1-2 h4-1'" &

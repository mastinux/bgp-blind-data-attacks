#!/usr/bin/env python

import sys
import os
import termcolor as T
import time
import datetime

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import lg, info, setLogLevel
from mininet.util import dumpNodeConnections, quietRun, moveIntf, waitListening
from mininet.cli import CLI
from mininet.node import Switch, OVSSwitch, Controller, RemoteController
from subprocess import Popen, PIPE, check_output
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

POX = '%s/pox/pox.py' % os.environ[ 'HOME' ]

ASES = 4
HOSTS_PER_AS = 3
BGP_CONVERGENCE_TIME = 0 #60
CAPTURING_WINDOW = 120

HUB_NAME = 'hub'
ATTACKER_NAME = 'atk1'

QUAGGA_STATE_DIR = '/var/run/quagga-1.2.4'

setLogLevel('info')
#setLogLevel('debug')

parser = ArgumentParser("Configure simple BGP network in Mininet.")
parser.add_argument('--sleep', default=3, type=int)
args = parser.parse_args()


def log(s, col="green"):
	print T.colored(s, col)


class Router(Switch):
	"""
	Defines a new router that is inside a network namespace so that the
	individual routing entries don't collide.
	"""
	ID = 0
	def __init__(self, name, **kwargs):
		kwargs['inNamespace'] = True
		Switch.__init__(self, name, **kwargs)
		Router.ID += 1
		self.switch_id = Router.ID

	@staticmethod
	def setup():
		return

	def start(self, controllers):
		pass

	def stop(self):
		self.deleteIntfs()

	def log(self, s, col="magenta"):
		print T.colored(s, col)


class SimpleTopo(Topo):
	"""
	The Autonomous System topology is a simple straight-line topology
	between AS1 -- AS2 -- AS3 -- AS4.
	"""
	def __init__(self):
		# Add default members to class.
		super(SimpleTopo, self ).__init__()

		num_hosts_per_as = HOSTS_PER_AS
		num_ases = ASES
		num_hosts = num_hosts_per_as * num_ases

		# The topology has one router per AS
		routers = []
		for i in xrange(num_ases):
			router = self.addSwitch('R%d' % (i+1))
			routers.append(router)

		# adding hosts to routers
		hosts = []
		for i in xrange(num_ases):
			router = 'R%d' % (i+1)
			for j in xrange(num_hosts_per_as):
				hostname = 'h%d-%d' % (i+1, j+1)
				host = self.addNode(hostname)
				hosts.append(host)
				self.addLink(router, host)

		self.addLink('R3', 'R4')
		
		# adding attacker to topology
		attacker_node = self.addNode(ATTACKER_NAME)
		hosts.append(attacker_node)

		for i in xrange(2):
			hub_name = HUB_NAME + '%s' % (i+1)

			# adding hub between routers and attacker
			self.addSwitch(hub_name, cls=OVSSwitch)
			self.addLink(hub_name, 'R%s' % (i+1))
			self.addLink(hub_name, 'R%s' % (i+2))
			self.addLink(hub_name, ATTACKER_NAME)

		return


def getIP(hostname):
	AS, idx = hostname.replace('h', '').split('-')
	AS = int(AS)

	ip = '%s.0.%s.1/24' % (10+AS, idx)

	return ip


def getGateway(hostname):
	AS, idx = hostname.replace('h', '').split('-')
	AS = int(AS)

	gw = '%s.0.%s.254' % (10+AS, idx)

	return gw


def startWebserver(net, hostname, text="Default web server"):
	host = net.getNodeByName(hostname)
	return host.popen("python webserver.py --text '%s'" % text, shell=True)


def startPOXHub():
	log("Starting POX RemoteController")
	os.system("python %s --verbose forwarding.hub > /tmp/hub.log 2>&1 &" % POX)

	log("Waiting %d seconds for pox RemoteController to start..." % args.sleep, col='cyan')
	sleep(args.sleep)


def stopPOXHub():
	log("Stopping POX RemoteController")
	os.system('pgrep -f pox.py | xargs kill -9')


def launch_attack(net, choice):
	log("launching attack", 'red')

	attacker_host = None

	# capturing packets on routers
	for router in net.switches:
		if choice == 2:
			if router.name == 'R2':
				router.cmd("tcpdump -i R2-eth4 -w /tmp/R2-eth4-blind-syn-attack.pcap &", shell=True)
				router.cmd("tcpdump -i R2-eth5 -w /tmp/R2-eth5-blind-syn-attack.pcap &", shell=True)

	# capturing files on hosts
	for host in net.hosts:
		if host.name == ATTACKER_NAME:
			attacker_host = host

			if choice == 2:
				attacker_host.popen("tcpdump -i atk1-eth0 -w /tmp/atk1-eth0-blind-syn-attack.pcap &", shell=True)

	# launching attack
	attacker_host.popen("python attacks.py %s > /tmp/attacks.log" % choice, shell=True)
	os.system('lxterminal -e "/bin/bash -c \'tail -f /tmp/attacks.log\'" > /dev/null 2>&1 &')

	# TODO sleep a proper time in order to collect enough packets
	sleep(args.sleep)


def init_quagga_state_dir():
	if not os.path.exists(QUAGGA_STATE_DIR):
		os.makedirs(QUAGGA_STATE_DIR)

	os.system('chown mininet:mininet %s' % QUAGGA_STATE_DIR)

	return


def main():
	os.system("rm -f /tmp/bgp-R?.pid /tmp/zebra-R?.pid 2> /dev/null")
	os.system("rm -f /tmp/R*.log /tmp/R*.pcap 2> /dev/null")
	os.system("rm -r logs/R*stdout 2> /dev/null")
	os.system("rm -r /tmp/hub.log /tmp/attacks.log /tmp/atk1*.pcap 2> /dev/null")

	os.system("mn -c > /dev/null 2>&1")

	os.system('pgrep zebra | xargs kill -9')
	os.system('pgrep bgpd | xargs kill -9')
	os.system('pgrep pox | xargs kill -9')
	os.system('pgrep -f webserver.py | xargs kill -9')

	init_quagga_state_dir()

	startPOXHub()

	net = Mininet(topo=SimpleTopo(), switch=Router)
	net.addController(name='poxController', controller=RemoteController, ip='127.0.0.1', port=6633)
	net.start()

	log("configuring hosts ...")
	for host in net.hosts:
		if host.name != ATTACKER_NAME:
			host.cmd("ifconfig %s-eth0 %s" % (host.name, getIP(host.name)))
			host.cmd("route add default gw %s" % (getGateway(host.name)))
		else:
			host.cmd("ifconfig %s-eth0 %s" % (host.name, '9.0.0.3'))
			host.cmd("ifconfig %s-eth1 %s" % (host.name, '9.0.1.3'))

	for i in xrange(ASES):
		log("Starting web server on h%s-1" % (i+1), 'yellow')
		startWebserver(net, 'h%s-1' % (i+1), "Web server on h%s-1" % (i+1))
	
	log("configuring routers ...")
	for router in net.switches:
		if HUB_NAME not in router.name:
			router.cmd("sysctl -w net.ipv4.ip_forward=1")
			router.waitOutput()

	log("Waiting %d seconds for sysctl changes to take effect..." % args.sleep, col='cyan')
	sleep(args.sleep)

	for router in net.switches:
		if HUB_NAME not in router.name:
			router.cmd("~/quagga-1.2.4/zebra/zebra -f conf/zebra-%s.conf -d -i /tmp/zebra-%s.pid > logs/%s-zebra-stdout 2>&1" % (router.name, router.name, router.name))
			router.waitOutput()
			router.cmd("~/quagga-1.2.4/bgpd/bgpd -f conf/bgpd-%s.conf -d -i /tmp/bgp-%s.pid > logs/%s-bgpd-stdout 2>&1" % (router.name, router.name, router.name), shell=True)
			router.waitOutput()
			log("Starting zebra and bgpd on %s" % router.name)

	log("Waiting %d seconds for BGP convergence (estimated %s)..."  % \
		(BGP_CONVERGENCE_TIME, (datetime.datetime.now()+datetime.timedelta(0, BGP_CONVERGENCE_TIME)).strftime("%H:%M:%S")), 'cyan')
	sleep(BGP_CONVERGENCE_TIME)

	choice = -1

	while choice != 0:
		choice = input("Choose:\n1) blind RST attack\n2) blind SYN attack\n3) blind UPDATE attack\n4) mininet CLI\n0) exit\n> ")

		if 0 < choice < 4:
			launch_attack(net, choice)
		elif choice == 4:
			CLI(net)

	"""
	log("Collecting data for %s seconds (estimated %s)..." % \
		(CAPTURING_WINDOW, (datetime.datetime.now()+datetime.timedelta(0,CAPTURING_WINDOW)).strftime("%H:%M:%S")), 'cyan')
	sleep(CAPTURING_WINDOW)
	#"""

	net.stop()

	stopPOXHub()

	os.system('pgrep zebra | xargs kill -9')
	os.system('pgrep bgpd | xargs kill -9')
	os.system('pgrep pox | xargs kill -9')
	os.system('pgrep -f webserver.py | xargs kill -9')


if __name__ == "__main__":
	main()

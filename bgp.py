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
BGP_CONVERGENCE_TIME = 60
CAPTURING_WINDOW = 120

HUB_NAME = 'hub'
ATTACKER_NAME = 'atk1'
TEST_HOST_NAME = 'testhost'

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
			hub_name = HUB_NAME + str(i+1)
			host_name = TEST_HOST_NAME + str(i+1)

			# adding bridge between R1 and R2
			self.addSwitch(hub_name, cls=OVSSwitch)

			self.addLink(hub_name, 'R%s' % (i+1))
			self.addLink(hub_name, 'R%s' % (i+2))

			# adding test host on bridge
			test_host_node = self.addNode(host_name)
			hosts.append(test_host_node)

			self.addLink(hub_name, host_name)

			self.addLink(hub_name, ATTACKER_NAME)

		return


def getIP(hostname):
	if hostname == ATTACKER_NAME:
		return '9.0.0.3'

	if hostname == (TEST_HOST_NAME + str(1)):
		return '9.0.0.4'

	if hostname == (TEST_HOST_NAME + str(2)):
		return '9.0.1.3'

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


def stopPOXHub():
	log("Stopping POX RemoteController")
	os.system('pgrep -f pox.py | xargs kill -9')


def launch_attack(attacker_host, choise):
	log("launching attack", 'red')

	attacker_host.popen("python attacker_attacks.py %s > /tmp/attacker_attacks.log 2>&1" % choise, shell=True)
	os.system('lxterminal -e "/bin/bash -c \'tail -f /tmp/attacker_attacks.log\'" &')

	log("attack launched", 'red')

def main():
	os.system("rm -f /tmp/R*.log /tmp/bgp-R?.pid /tmp/zebra-R?.pid 2> /dev/null")
	os.system("rm -r logs/*stdout /tmp/hub.log /tmp/attacker_attacks.log /tmp/testhost* 2> /dev/null")
	os.system("mn -c > /dev/null 2>&1")
	os.system("killall -9 zebra bgpd > /dev/null 2>&1")
	os.system('pgrep -f webserver.py | xargs kill -9')

	startPOXHub()

	net = Mininet(topo=SimpleTopo(), switch=Router)
	net.addController(name='poxController', controller=RemoteController, ip='127.0.0.1', port=6633)
	net.start()

	# CONFIGURING HOSTS

	attacker_host = None
	# insider_host = None

	for host in net.hosts:
		# host.setIP(getIP(host.name))
		host.cmd("ifconfig %s-eth0 %s" % (host.name, getIP(host.name)))

		if host.name != ATTACKER_NAME and TEST_HOST_NAME not in host.name:
			# host.setDefaultRoute(getGateway(host.name))
			host.cmd("route add default gw %s" % (getGateway(host.name)))

		if host.name == ATTACKER_NAME:
			host.cmd("ifconfig %s-eth0 %s" % (host.name, '9.0.0.3'))
			host.cmd("ifconfig %s-eth1 %s" % (host.name, '9.0.1.3'))
			attacker_host = host

		# if host.name == 'h1-3':
		#	insider_host = host

	os.system('./testhost1_tcpdump.sh > /tmp/testhost1_tcpdump.log 2>&1 &')
	os.system('./testhost2_tcpdump.sh > /tmp/testhost2_tcpdump.log 2>&1 &')

	for i in xrange(ASES):
		log("Starting web server on h%s-1" % (i+1), 'yellow')
		startWebserver(net, 'h%s-1' % (i+1), "Web server on h%s-1" % (i+1))

	# CONFIGURING ROUTERS

	for router in net.switches:
		if HUB_NAME not in router.name:
			router.cmd("sysctl -w net.ipv4.ip_forward=1")
			router.waitOutput()

	log("Waiting %d seconds for sysctl changes to take effect..." % args.sleep, col='cyan')
	sleep(args.sleep)

	for router in net.switches:
		if HUB_NAME not in router.name:
			router.cmd("/usr/lib/quagga/zebra -f conf/zebra-%s.conf -d -i /tmp/zebra-%s.pid > logs/%s-zebra-stdout 2>&1" % (router.name, router.name, router.name))
			router.waitOutput()
			router.cmd("/usr/lib/quagga/bgpd -f conf/bgpd-%s.conf -d -i /tmp/bgp-%s.pid > logs/%s-bgpd-stdout 2>&1" % (router.name, router.name, router.name), shell=True)
			router.waitOutput()
			log("Starting zebra and bgpd on %s" % router.name)

	log("Waiting %d seconds for BGP convergence (estimated %s)..."  % \
		(BGP_CONVERGENCE_TIME, (datetime.datetime.now()+datetime.timedelta(0, BGP_CONVERGENCE_TIME)).strftime("%H:%M:%S")), 'cyan')
	sleep(BGP_CONVERGENCE_TIME)

	choise = -1

	while choise != 0:
		choise = input("Choose the attack:\n1) blind RST attack\n2) blind SYN attack\n3) blind UPDATE attack\n0) exit\n> ")

		if choise != 0:
			launch_attack(attacker_host, choise)

	"""
	log("Collecting data for %s seconds (estimated %s)..." % \
		(CAPTURING_WINDOW, (datetime.datetime.now()+datetime.timedelta(0,CAPTURING_WINDOW)).strftime("%H:%M:%S")), 'cyan')
	sleep(CAPTURING_WINDOW)
	#"""

	#CLI(net)
	net.stop()

	stopPOXHub()

	os.system("killall -9 zebra bgpd")
	os.system('pgrep -f webserver.py | xargs kill -9')


if __name__ == "__main__":
	main()

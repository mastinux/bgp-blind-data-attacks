#!/usr/bin/env python

import sys
import os

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import lg, info, setLogLevel
from mininet.util import dumpNodeConnections, quietRun, moveIntf, waitListening
from mininet.cli import CLI
from mininet.node import Switch, OVSSwitch, Controller, RemoteController, Node
from subprocess import Popen, PIPE, check_output
from multiprocessing import Process
from argparse import ArgumentParser
from utils import log, log2

POX = '%s/pox/pox.py' % os.environ[ 'HOME' ]

ASES = 4
HOSTS_PER_AS = 3
BGP_CONVERGENCE_TIME = 15 * 2 # <keepalive> * 2

HUB_NAME = 'hub'
ATTACKER_NAME = 'atk1'

QUAGGA_STATE_DIR = '/var/run/quagga-1.2.4'

setLogLevel('info')
#setLogLevel('debug')

parser = ArgumentParser("Configure simple BGP network in Mininet.")
parser.add_argument('--sleep', default=3, type=int)
args = parser.parse_args()


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
		for i in self.intfList():
			i.setMAC(get_MAC(i.name))

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


def get_MAC(interface):
	if interface == 'lo':
		return None

	# R2-eth0 or atk1-eth0
	c = ''
	l = interface.split('-')
	x = ''

	if 'R' in l[0]:
		c = l[0].replace('R', '')
	else:
		c = 'a'

	couple = c * 2
	identity = '0' + l[1].replace('eth', '')
	s = ':'.join([couple for _ in range(5)]) + ':' + identity

	#print interface, '->', s

	return s


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

	log2("pox RemoteController to start", args.sleep, col='cyan')


def stopPOXHub():
	log("Stopping POX RemoteController")
	os.system('pgrep -f pox.py | xargs kill -9')


def launch_attack(net, choice, remote_flag):
	log("Launching attack\nCheck opened terminal", 'red')

	attacker_host_eth0_mac_address = None
	attacker_host_eth1_mac_address = None
	r2_eth4_mac_address = None
	r2_eth5_mac_address = None

	# retrieving attack host
	for host in net.hosts:
		if host.name == ATTACKER_NAME:
			attacker_host = host

			for i in host.intfList():
				if 'eth0' in i.name:
					attacker_host_eth0_mac_address = i.MAC()
				if 'eth1' in i.name:
					attacker_host_eth1_mac_address = i.MAC()

	# retrieving R2-eth4 MAC address
	for router in net.switches:
		if router.name == 'R2':
			for i in router.intfList():
				if 'eth4' in i.name:
					r2_eth4_mac_address = i.MAC()
				if 'eth5' in i.name:
					r2_eth5_mac_address = i.MAC()

	assert attacker_host_eth0_mac_address is not None
	assert attacker_host_eth1_mac_address is not None
	assert r2_eth4_mac_address is not None
	assert r2_eth5_mac_address is not None

	# launching attack
	attacker_host.popen("python attacks.py %s %s %s %s %s %s > /tmp/attacks.out 2> /tmp/attacks.err &" % \
		(choice, remote_flag, attacker_host_eth0_mac_address, attacker_host_eth1_mac_address, r2_eth4_mac_address, r2_eth5_mac_address), shell=True)

	os.system('lxterminal -e "/bin/bash -c \'echo --- attacks.out content ---; echo; tail -f /tmp/attacks.out\'" > /dev/null 2>&1 &')
	os.system('lxterminal -e "/bin/bash -c \'echo --- attacks.err content ---; echo; tail -f /tmp/attacks.err\'" > /dev/null 2>&1 &')


def init_quagga_state_dir():
	if not os.path.exists(QUAGGA_STATE_DIR):
		os.makedirs(QUAGGA_STATE_DIR)

	os.system('chown mininet:mininet %s' % QUAGGA_STATE_DIR)

	return

	
def main():
	os.system("reset")

	os.system("rm -f /tmp/bgp-R?.pid /tmp/zebra-R?.pid 2> /dev/null")
	os.system("rm -f /tmp/R*.log /tmp/R*.pcap 2> /dev/null")
	os.system("rm logs/R*stdout 2> /dev/null")
	os.system("rm /tmp/hub.log /tmp/c*.log /tmp/attacks.* /tmp/atk1*.pcap 2> /dev/null")
	os.system("rm /tmp/tcpdump*.out /tmp/tcpdump*.err 2> /dev/null")
	os.system("rm /tmp/R*-complete.out /tmp/R*-complete.err 2> /dev/null")

	os.system("mn -c > /dev/null 2>&1")

	os.system('pgrep zebra | xargs kill -9')
	os.system('pgrep bgpd | xargs kill -9')
	os.system('pgrep pox | xargs kill -9')
	os.system('pgrep -f webserver.py | xargs kill -9')

	init_quagga_state_dir()

	startPOXHub()

	net = Mininet(topo=SimpleTopo(), switch=Router)
	net.addController(name='poxController', controller=RemoteController, \
		ip='127.0.0.1', port=6633)
	net.start()

	log("Configuring hosts ...")
	for host in net.hosts:
		if host.name != ATTACKER_NAME:
			host.cmd("ifconfig %s-eth0 %s" % (host.name, getIP(host.name)))
			host.cmd("route add default gw %s" % (getGateway(host.name)))
		else:
			host.cmd("ifconfig %s-eth0 %s" % (host.name, '9.0.0.3'))
			host.cmd("ifconfig %s-eth1 %s" % (host.name, '9.0.1.3'))

			for i in host.intfList():
				i.setMAC(get_MAC(i.name))

			host.cmd("tcpdump -i atk1-eth0 -w /tmp/atk1-eth0-blind-attack.pcap not arp > /tmp/tcpdump-atk1-eth0.out 2> /tmp/tcpdump-atk1-eth0.err &", shell=True)
			host.cmd("tcpdump -i atk1-eth1 -w /tmp/atk1-eth1-blind-attack.pcap not arp > /tmp/tcpdump-atk1-eth1.out 2> /tmp/tcpdump-atk1-eth1.err &", shell=True)

	for i in xrange(ASES):
		log("Starting web server on h%s-1" % (i+1), 'yellow')
		startWebserver(net, 'h%s-1' % (i+1), "Web server on h%s-1" % (i+1))
	
	log("Configuring routers ...")
	for router in net.switches:

		if HUB_NAME not in router.name:
			# 0 = no RPF
			# 1 = RPF strict mode
			# 2 = RPF loose mode
			router.cmd("sysctl -w net.ipv4.conf.all.rp_filter=2")

			router.cmd("sysctl -w net.ipv4.ip_forward=1")
			router.waitOutput()

			if router.name == 'R2':
				router.cmd("tcpdump -i R2-eth4 -w /tmp/R2-eth4-complete.pcap not arp > /tmp/R2-eth4-complete.out 2> /tmp/R2-eth4-complete.err &", shell=True)

	log2("sysctl changes to take effect", args.sleep, col='cyan')

	for router in net.switches:
		if HUB_NAME not in router.name:
			router.cmd("~/quagga-1.2.4/zebra/zebra -f conf/zebra-%s.conf -d -i /tmp/zebra-%s.pid > logs/%s-zebra-stdout 2>&1" % \
				(router.name, router.name, router.name))
			router.waitOutput()

			router.cmd("~/quagga-1.2.4/bgpd/bgpd -f conf/bgpd-%s.conf -d -i /tmp/bgp-%s.pid > logs/%s-bgpd-stdout 2>&1" % \
				(router.name, router.name, router.name), shell=True)
			router.waitOutput()

			log("Starting zebra and bgpd on %s" % router.name)

	log2("BGP convergence", BGP_CONVERGENCE_TIME, 'cyan')

	choice = -1

	while choice != 0:
		choice = raw_input("Choose:\n1) blind RST attack\n2) blind SYN attack\n3) blind UPDATE attack\n4) mininet CLI\n0) exit\n> ")

		if choice != '':
			choice = int(choice)

			if 0 < choice < 4:
				#remote_flag = -1
				#while remote_flag < 0 or remote_flag > 1:
				#	remote_flag = int(raw_input("Local (0) or Remote (1) attack? "))
				remote_flag = 1

				launch_attack(net, choice, remote_flag)

				for router in net.switches:
					if HUB_NAME not in router.name:
						if router.name == 'R2':
							router.cmd("tcpdump -i R2-eth4 -w /tmp/R2-eth4-blind-attack.pcap not arp > /tmp/tcpdump-R2-eth4.out 2> /tmp/tcpdump-R2-eth4.err &", shell=True)
							router.cmd("tcpdump -i R2-eth5 -w /tmp/R2-eth5-blind-attack.pcap not arp > /tmp/tcpdump-R2-eth5.out 2> /tmp/tcpdump-R2-eth5.err &", shell=True)
			elif choice == 4:
				CLI(net)

	net.stop()

	stopPOXHub()

	os.system('pgrep zebra | xargs kill -9')
	os.system('pgrep bgpd | xargs kill -9')
	os.system('pgrep pox | xargs kill -9')
	os.system('pgrep -f webserver.py | xargs kill -9')

	# os.system('sudo wireshark /tmp/atk1-eth0-blind-attack.pcap -Y \'not ipv6\' &')
	# os.system('sudo wireshark /tmp/atk1-eth1-blind-attack.pcap -Y \'not ipv6\' &')
	os.system('sudo wireshark /tmp/R2-eth4-blind-attack.pcap -Y \'not ipv6\' &')
	os.system('sudo wireshark /tmp/R2-eth5-blind-attack.pcap -Y \'not ipv6\' &')


if __name__ == "__main__":
	main()

#!/usr/bin/env python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import lg, info, setLogLevel
from mininet.util import dumpNodeConnections, quietRun, moveIntf
from mininet.cli import CLI
from mininet.node import Switch, OVSKernelSwitch

from subprocess import Popen, PIPE, check_output
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

import sys
import os
import termcolor as T
import time

setLogLevel('info')

parser = ArgumentParser("Configure simple BGP network in Mininet.")
# no rogue AS - only an attacker host
#parser.add_argument('--rogue', action="store_true", default=False)
parser.add_argument('--sleep', default=3, type=int)
args = parser.parse_args()

#FLAGS_rogue_as = args.rogue
#ROGUE_AS_NAME = 'R4'

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
        # Delete all of our interfaces.
        self.deleteIntfs()

    def log(self, s, col="magenta"):
        print T.colored(s, col)


class SimpleTopo(Topo):
    """
    The Autonomous System topology is a simple straight-line topology 
    between AS1 -- AS2 -- AS3 -- AS4. 
    The host attacker (ATK1) is between R1 and R2. ATK1, R1 e R2 are connected 
    to the same hub.
    """

    def __init__(self):
        # Add default members to class.
        super(SimpleTopo, self ).__init__()
        num_hosts_per_as = 3
        num_ases = 4
        num_hosts = num_hosts_per_as * num_ases

        # The topology has one router per AS
        routers = []

        # adding routers
        for i in xrange(num_ases):
            router = self.addSwitch('R%d' % (i+1))
	    routers.append(router)

        hosts = []

        # adding hosts
        for i in xrange(num_ases):
            router = 'R%d' % (i+1)

            for j in xrange(num_hosts_per_as):
                hostname = 'h%d-%d' % (i+1, j+1)
                host = self.addNode(hostname)
                hosts.append(host)
                self.addLink(router, host)

        # adding links (R1-R2) (R2-R3) (R3-R4)
        for i in xrange(num_ases):
            self.addLink('R%d' % (i+1), 'R%d' % (i+2))

        # no rogue AS - only an attacker host
        """
        # rogue AS
        routers.append(self.addSwitch('R4'))

        # adding hosts to rogue AS
        for j in xrange(num_hosts_per_as):
            hostname = 'h%d-%d' % (4, j+1)
            host = self.addNode(hostname)
            hosts.append(host)
            self.addLink('R4', hostname)

        # This MUST be added at the end
        # adding link (R1-R4)
        self.addLink('R1', 'R4')
        """

		# TODO add an hub between R1 and R2

        return


def getIP(hostname):
    # retrieve host address from its name

    AS, idx = hostname.replace('h', '').split('-')
    AS = int(AS)
    if AS == 4:
        AS = 3
    ip = '%s.0.%s.1/24' % (10+AS, idx)
    return ip


def getGateway(hostname):
    # retrieve gateway address from host name

    AS, idx = hostname.replace('h', '').split('-')
    AS = int(AS)
    # This condition gives AS4 the same IP range as AS3 so it can be an
    # attacker.
    if AS == 4:
        AS = 3
    gw = '%s.0.%s.254' % (10+AS, idx)
    return gw


def startWebserver(net, hostname, text="Default web server"):
    host = net.getNodeByName(hostname)
    return host.popen("python webserver.py --text '%s'" % text, shell=True)


def main():
    # clearing logs
    os.system("rm -f /tmp/R*.log /tmp/R*.pid logs/*")

    # launching mininet
    os.system("mn -c >/dev/null 2>&1")

    # killing zebra and bgpd
    os.system("killall -9 zebra bgpd > /dev/null 2>&1")

    # killing the webserver
    os.system('pgrep -f webserver.py | xargs kill -9')

    net = Mininet(topo=SimpleTopo(), switch=Router)
    net.start()

    for router in net.switches:
        # enabling IPv4 forwarding on router
        router.cmd("sysctl -w net.ipv4.ip_forward=1")
        router.waitOutput()

    log("Waiting %d seconds for sysctl changes to take effect..." % args.sleep)
    sleep(args.sleep)

    for router in net.switches:
        if router.name == ROGUE_AS_NAME and not FLAGS_rogue_as:
            continue

        # configuring routing entries with zebra
        router.cmd("/usr/lib/quagga/zebra -f conf/zebra-%s.conf -d -i /tmp/zebra-%s.pid > logs/%s-zebra-stdout 2>&1" % (router.name, router.name, router.name))
        router.waitOutput()
        # configuring bgpd (routing deamon) with quagga
        router.cmd("/usr/lib/quagga/bgpd -f conf/bgpd-%s.conf -d -i /tmp/bgp-%s.pid > logs/%s-bgpd-stdout 2>&1" % (router.name, router.name, router.name), shell=True)
        router.waitOutput()
        log("Starting zebra and bgpd on %s" % router.name)

    for host in net.hosts:
        # configuring host IP address
        host.cmd("ifconfig %s-eth0 %s" % (host.name, getIP(host.name)))
        # configuring default gateway
        host.cmd("route add default gw %s" % (getGateway(host.name)))

    log("Starting web servers", 'yellow')
    startWebserver(net, 'h3-1', "Default web server")
    startWebserver(net, 'h4-1', "*** Attacker web server ***")

    CLI(net)
    net.stop()
    os.system("killall -9 zebra bgpd")
    os.system('pgrep -f webserver.py | xargs kill -9')

if __name__ == "__main__":
    main()

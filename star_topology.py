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

NUM_HOSTS_PER_SWITCH = 8
NUM_SWITCHES = 3

setLogLevel('info')

parser = ArgumentParser("Configure simple switched network in Mininet.")
parser.add_argument('--sleep', default=3, type=int)
args = parser.parse_args()

def log(s, col="green"):
    print T.colored(s, col)

class SimpleTopo(Topo):
    """
    The topology is a simple star topology
    one switch in the center and 5 hosts connected
    """

    def __init__(self):
        # Add default members to class.
        super(SimpleTopo, self ).__init__()

        num_hosts_per_switch = NUM_HOSTS_PER_SWITCH
        num_switches = NUM_SWITCHES
        num_hosts = num_hosts_per_switch * num_switches

        switches = []
        for i in xrange(num_switches):
            switch = self.addSwitch('s%d' % (i+1))
            switches.append(switch)

        hosts = []
        for i in xrange(num_switches):
            switch = 's%d' % (i+1)
            for j in xrange(num_hosts_per_switch):
                hostname = 'h%d-%d' % (1, (i*NUM_HOSTS_PER_SWITCH)+j+1)
                print hostname
                host = self.addNode(hostname)
                hosts.append(host)
                self.addLink(switch, host)

        for i in xrange(num_switches-1):
            self.addLink('s%d' % (i+1), 's%d' % (i+2))

        return


def getIP(hostname):
    AS, idx = hostname.replace('h', '').split('-')
    AS = int(AS)
    ip = '%s.0.1.%s/24' % (10+AS, idx)
    return ip


def getGateway(hostname):
    AS, idx = hostname.replace('h', '').split('-')
    AS = int(AS)
    gw = '%s.0.1.254' % (10+AS)
    return gw


def startWebserver(net, hostname, text="Default web server"):
    host = net.getNodeByName(hostname)
    return host.popen("python webserver.py --text '%s'" % text, shell=True)


def main():
    os.system("rm -f /tmp/R*.log /tmp/R*.pid logs/*stdout")
    os.system("mn -c >/dev/null 2>&1")
    os.system("killall -9 zebra bgpd > /dev/null 2>&1")
    os.system('pgrep -f webserver.py | xargs kill -9')

    net = Mininet(topo=SimpleTopo())
    net.start()
    for switch in net.switches:
        switch.cmd("sysctl -w net.ipv4.ip_forward=1")
        switch.waitOutput()

    log("Waiting %d seconds for sysctl changes to take effect..." % args.sleep)
    sleep(args.sleep)

    for host in net.hosts:
        print "configuring host ", host.name
        print "IP ", getIP(host.name)
        print "gw ", getGateway(host.name)
        host.cmd("ifconfig %s-eth0 %s" % (host.name, getIP(host.name)))
        host.cmd("route add default gw %s" % (getGateway(host.name)))

    log("Starting web servers", 'yellow')
    startWebserver(net, 'h1-16', "Default web server")
    startWebserver(net, 'h1-24', "*** Attacker web server ***")

    CLI(net)
    net.stop()
    os.system('pgrep -f webserver.py | xargs kill -9')


if __name__ == "__main__":
    main()

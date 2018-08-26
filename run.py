#!/usr/bin/env python
from argparse import ArgumentParser
import sys
import os
import termcolor as T
from subprocess import Popen, PIPE, check_output
import re

parser = ArgumentParser("Connect to a mininet node and run a command")
parser.add_argument('--node',
                    help="The node's name (e.g., h1, h2, etc.)")
parser.add_argument('--list', action="store_true", default=False,
                    help="List all running nodes.")
parser.add_argument('--cmd', default='ifconfig',
                    nargs="+",
                    help="Command to run inside node.")

parser.add_argument('--snode',
                    help="The source node's name (e.g., h1, h2, etc.)")
parser.add_argument('--dnode',
                    help="The destination node's name (e.g., h1, h2, etc.)")

FLAGS = parser.parse_args()
node_pat = re.compile(r'.*bash --norc --noediting -is mininet:(.*)')


def list_nodes(do_print=False):
    # prints mininet node name with PID

    cmd = 'ps aux'
    proc = Popen(cmd.split(), stdout=PIPE)
    out, err = proc.communicate()
    # Mapping from name to pid.
    ret = {}
    for line in out.split('\n'):
        match = node_pat.match(line)
        if not match:
            continue
        name = match.group(1)
        pid = line.split()[1]
        if do_print:
            print "name: %6s, pid: %6s" % (name, pid)
        ret[name] = pid
    return ret


def main():
    if FLAGS.list:
        list_nodes(do_print=True)
        return

    if FLAGS.snode and FLAGS.dnode:
        pid_by_name = list_nodes()

        spid = pid_by_name.get(FLAGS.snode)
        if spid is None:
            print "node `%s' not found" % (FLAGS.snode)
            sys.exit(1)

        dpid = pid_by_name.get(FLAGS.dnode)
        if dpid is None:
            print "node `%s' not found" % (FLAGS.dnode)
            sys.exit(1)

        dnode_IP_address = check_output("mnexec -a %s %s" % (dpid, 'hostname -I'), shell=True)

        cmd = ' '.join(FLAGS.cmd) + ' ' + dnode_IP_address

        os.system("mnexec -a %s %s" % (spid, cmd))

    elif FLAGS.node:
        pid_by_name = list_nodes()
        pid = pid_by_name.get(FLAGS.node)
        if pid is None:
            print "node `%s' not found" % (FLAGS.node)
            sys.exit(1)

        cmd = ' '.join(FLAGS.cmd)

        os.system("mnexec -a %s %s" % (pid, cmd))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

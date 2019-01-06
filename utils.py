import sys
import termcolor
import datetime
import time


def log(s, col="green"):
	"""
		grey
		red
		green
		yellow
		blue
		magenta
		cyan
		white
	"""
	print termcolor.colored('[%s] %s' % \
		(datetime.datetime.now().strftime("%H:%M:%S"), s), col)

	sys.stdout.flush()


def log2(reason, interval=10, col="green"):
	log('Waiting %s seconds for %s ...' % (interval, reason) , col)

	sys.stdout.flush()

	time.sleep(interval)


def string_to_hex(s):
	return ':'.join(x.encode('hex') for x in s) + ' len:' + str(len(s))


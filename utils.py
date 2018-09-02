import sys
import termcolor as T
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
	print T.colored('[%s] %s' % \
		(datetime.datetime.now().strftime("%H:%M:%S"), s), col)

	sys.stdout.flush()


def log2(reason, interval=10, col="green"):
	log('Waiting %s seconds for %s ...' % (interval, reason) , col)

	time.sleep(interval)


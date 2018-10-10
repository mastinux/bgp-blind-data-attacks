from utils import string_to_hex

from scapy.all import *

load_contrib("bgp")


class CustomBGPPathAttribute(BGPPathAttribute):

	@classmethod
	def post_build(self, p, pay):
		#print 'entering custom post_build'
		#print 'p\t', string_to_hex(p)
		#print 'pay\t', string_to_hex(pay)

		if self.attr_len is None:
			#print 'attr_len was None'
			l = len(p) - 3 # 3 is regular length with no additional options
			p = p[:2] + struct.pack("!B",l)  +p[3:]
		
		if p[0] == '\x50': # Extened Leght
			#print 'entering Extended length'
			p = p[:2] + '\x00' + p[2:]

		ret = p + pay

		#print 'ret\t', string_to_hex(ret)

		return ret

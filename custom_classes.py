from scapy.all import *

class CustomBGPPathAttribute(BGPPathAttribute):
	# TODO override post_build method in order to support Extended-Length

	@classmethod
	def post_build(self, p, pay):
		ret = super(CustomBGPPathAttribute, self).post_build(p, pay)

		# add your code here

		return ret

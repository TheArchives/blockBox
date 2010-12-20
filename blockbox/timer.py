# blockBox is Copyright 2009-2010 of the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import threading, time

class ResettableTimer(threading.Thread):
	"""
	The ResettableTimer class is a timer whose counting loop can be reset
	arbitrarily. Its duration is configurable. Commands can be specified
	for both expiration and update. Its update resolution can also be
	specified. Resettable timer keeps counting until the "run" method
	is explicitly killed with the "kill" method.
	"""

	def __init__(self, maxtime, inc, expire , update=None):
		"""
		@param maxtime: time in seconds before expiration after resetting
						in seconds
		@param expire: function called when timer expires
		@param inc: amount by which timer increments before
					updating in seconds, default is maxtime/2
		@param expire: function called when timer completes
		@param update: function called when timer updates
		"""
		self.maxtime = maxtime
		self.expire = expire
		self.inc = inc
		if update:
			self.update = update
		else:
			self.update = lambda c : None
		self.counter = 0
		self.stop = False
		threading.Thread.__init__(self)
		self.setDaemon(True)

	def set_counter(self, t):
		"""
		Set self.counter to t.
		@param t: new counter value
		"""
		self.counter = t

	def kill(self):
		"""
		Will stop the counting loop before next update.
		"""
		self.stop = True
		self.counter = self.maxtime

	def reset(self):
		"""
		Fully rewinds the timer and makes the timer active, such that
		the expire and update commands will be called when appropriate.
		"""
		self.counter = 0
		self.stop = False

	def run(self):
		"""
		Run the timer loop.
		"""
		self.counter = 0
		while self.counter < self.maxtime and not self.stop:
			self.counter += self.inc
			time.sleep(self.inc)
			self.update(self.counter)
		if not self.stop:
			self.expire()
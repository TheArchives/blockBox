# blockBox is Copyright 2009-2010 of the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

class Deferred(object):
	"""
	Simple implementation of the Deferred pattern - a way to do
	asynchronous operations in a simple single-threaded manner.
	"""

	def __init__(self):
		self.callbacks = []
		self.errbacks = []
		self.stepbacks = []
		self.called_back = None
		self.erred_back = None
		self.stepped_back = None
	def addCallback(self, func, *args, **kwargs):
		"Adds a callback for success."
		if self.called_back is None:
			self.callbacks.append((func, args, kwargs))
		else:
			self.merge_call(func, args, self.called_back[0], kwargs, self.called_back[1])
	def addErrback(self, func, *args, **kwargs):
		"Adds a callback for error."
		if self.erred_back is None:
			self.errbacks.append((func, args, kwargs))
		else:
			self.merge_call(func, args, self.erred_back[0], kwargs, self.erred_back[1])
	def addStepback(self, func, *args, **kwargs):
		"Adds a callback for algorithm steps."
		self.stepbacks.append((func, args, kwargs))
		if self.stepped_back is not None:
			self.merge_call(func, args, self.stepped_back[0], kwargs, self.stepped_back[1])
	def merge_call(self, func, args1, args2, kwargs1, kwargs2):
		"Merge two function call definitions together sensibly, and run them."
		kwargs1.update(kwargs2)
		func(*(args1+args2), **kwargs1)
	def callback(self, *args, **kwargs):
		"Send a successful-callback signal."
		for func, fargs, fkwargs in self.callbacks:
			self.merge_call(func, fargs, args, fkwargs, kwargs)
		self.called_back = (args, kwargs)
	def errback(self, *args, **kwargs):
		"Send an error-callback signal."
		for func, fargs, fkwargs in self.errbacks:
			self.merge_call(func, fargs, args, fkwargs, kwargs)
		self.erred_back = (args, kwargs)
	def stepback(self, *args, **kwargs):
		"Send a step-callback signal."
		for func, fargs, fkwargs in self.stepbacks:
			self.merge_call(func, fargs, args, fkwargs, kwargs)
		self.stepped_back = (args, kwargs)

#    iCraft is Copyright 2010 both
#
#    The Archives team:
#                   <Adam Guy> adam@adam-guy.com AKA "Adam01"
#                   <Andrew Godwin> andrew@aeracode.org AKA "Aera"
#                   <Dylan Lukes> lukes.dylan@gmail.com AKA "revenant"
#                   <Gareth Coles> colesgareth2@hotmail.com AKA "gdude2002"
#
#    And,
#
#    The iCraft team:
#                   <Andrew Dolgov> fox@bah.org.ru AKA "gothfox"
#                   <Andrew Horn> Andrew@GJOCommunity.com AKA "AndrewPH"
#                   <Brad Reardon> brad@bradness.co.cc AKA "PixelEater"
#                   <Clay Sweetser> CDBKJmom@aol.com AKA "Varriount"
#                   <James Kirslis> james@helplarge.com AKA "iKJames"
#                   <Jason Sayre> admin@erronjason.com AKA "erronjason"
#                   <Joseph Connor> destroyerx100@gmail.com AKA "destroyerx1"
#                   <Nick Tolrud> ntolrud@yahoo.com AKA "ntfwc"
#                   <Noel Benzinger> ronnygmod@gmail.com AKA "Dwarfy"
#                   <Randy Lyne> qcksilverdragon@gmail.com AKA "goober"
#                   <Willem van der Ploeg> willempieeploeg@live.nl AKA "willempiee"
#
#    iCraft is licensed under the Creative Commons
#    Attribution-NonCommercial-ShareAlike 3.0 Unported License. 
#    To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#    Or, send a letter to Creative Commons, 171 2nd Street,
#    Suite 300, San Francisco, California, 94105, USA.

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

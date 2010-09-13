# -*- test-case-name: lib.twisted.test.test_htb -*-
#
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
from __future__ import nested_scopes
__version__ = '$Revision: 1.5 $'[11:-2]
from time import time
from lib.zope.interface import implements, Interface
from lib.twisted.protocols import pcp

class Bucket:
    maxburst = None
    rate = None
    _refcount = 0

    def __init__(self, parentBucket=None):
        self.content = 0
        self.parentBucket=parentBucket
        self.lastDrip = time()

    def add(self, amount):
        self.drip()
        if self.maxburst is None:
            allowable = amount
        else:
            allowable = min(amount, self.maxburst - self.content)
        if self.parentBucket is not None:
            allowable = self.parentBucket.add(allowable)
        self.content += allowable
        return allowable

    def drip(self):
        if self.parentBucket is not None:
            self.parentBucket.drip()

        if self.rate is None:
            self.content = 0
            return True
        else:
            now = time()
            deltaT = now - self.lastDrip
            self.content = long(max(0, self.content - deltaT * self.rate))
            self.lastDrip = now
            return False

class IBucketFilter(Interface):
    def getBucketFor(*somethings, **some_kw):

class HierarchicalBucketFilter:
    implements(IBucketFilter)
    bucketFactory = Bucket
    sweepInterval = None

    def __init__(self, parentFilter=None):
        self.buckets = {}
        self.parentFilter = parentFilter
        self.lastSweep = time()

    def getBucketFor(self, *a, **kw):
        if ((self.sweepInterval is not None)
            and ((time() - self.lastSweep) > self.sweepInterval)):
            self.sweep()

        if self.parentFilter:
            parentBucket = self.parentFilter.getBucketFor(self, *a, **kw)
        else:
            parentBucket = None

        key = self.getBucketKey(*a, **kw)
        bucket = self.buckets.get(key)
        if bucket is None:
            bucket = self.bucketFactory(parentBucket)
            self.buckets[key] = bucket
        return bucket

    def getBucketKey(self, *a, **kw):
        return None

    def sweep(self):
        for key, bucket in self.buckets.items():
            if (bucket._refcount == 0) and bucket.drip():
                del self.buckets[key]

        self.lastSweep = time()

class FilterByHost(HierarchicalBucketFilter):
    sweepInterval = 60 * 20
    def getBucketKey(self, transport):
        return transport.getPeer()[1]

class FilterByServer(HierarchicalBucketFilter):
    sweepInterval = None

    def getBucketKey(self, transport):
        return transport.getHost()[2]

class ShapedConsumer(pcp.ProducerConsumerProxy):
    iAmStreaming = False

    def __init__(self, consumer, bucket):
        pcp.ProducerConsumerProxy.__init__(self, consumer)
        self.bucket = bucket
        self.bucket._refcount += 1

    def _writeSomeData(self, data):
        amount = self.bucket.add(len(data))
        return pcp.ProducerConsumerProxy._writeSomeData(self, data[:amount])

    def stopProducing(self):
        pcp.ProducerConsumerProxy.stopProducing(self)
        self.bucket._refcount -= 1

class ShapedTransport(ShapedConsumer):
    iAmStreaming = False
    def __getattr__(self, name):
        return getattr(self.consumer, name)

class ShapedProtocolFactory:
    def __init__(self, protoClass, bucketFilter):
        self.protocol = protoClass
        self.bucketFilter = bucketFilter

    def __call__(self, *a, **kw):
        proto = self.protocol(*a, **kw)
        origMakeConnection = proto.makeConnection
        def makeConnection(transport):
            bucket = self.bucketFilter.getBucketFor(transport)
            shapedTransport = ShapedTransport(transport, bucket)
            return origMakeConnection(shapedTransport)
        proto.makeConnection = makeConnection
        return proto

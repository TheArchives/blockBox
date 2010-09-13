# -*- test-case-name: twisted.internet.test.test_pollingfile -*-
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
from zope.interface import implements
from twisted.internet.interfaces import IConsumer, IPushProducer
MIN_TIMEOUT = 0.000000001
MAX_TIMEOUT = 0.1

class _PollableResource:
    active = True
    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

class _PollingTimer:
    def __init__(self, reactor):
        self.reactor = reactor
        self._resources = []
        self._pollTimer = None
        self._currentTimeout = MAX_TIMEOUT
        self._paused = False

    def _addPollableResource(self, res):
        self._resources.append(res)
        self._checkPollingState()

    def _checkPollingState(self):
        for resource in self._resources:
            if resource.active:
                self._startPolling()
                break
        else:
            self._stopPolling()

    def _startPolling(self):
        if self._pollTimer is None:
            self._pollTimer = self._reschedule()

    def _stopPolling(self):
        if self._pollTimer is not None:
            self._pollTimer.cancel()
            self._pollTimer = None

    def _pause(self):
        self._paused = True

    def _unpause(self):
        self._paused = False
        self._checkPollingState()

    def _reschedule(self):
        if not self._paused:
            return self.reactor.callLater(self._currentTimeout, self._pollEvent)

    def _pollEvent(self):
        workUnits = 0.
        anyActive = []
        for resource in self._resources:
            if resource.active:
                workUnits += resource.checkWork()
                if resource.active:
                    anyActive.append(resource)

        newTimeout = self._currentTimeout
        if workUnits:
            newTimeout = self._currentTimeout / (workUnits + 1.)
            if newTimeout < MIN_TIMEOUT:
                newTimeout = MIN_TIMEOUT
        else:
            newTimeout = self._currentTimeout * 2.
            if newTimeout > MAX_TIMEOUT:
                newTimeout = MAX_TIMEOUT
        self._currentTimeout = newTimeout
        if anyActive:
            self._pollTimer = self._reschedule()

import win32pipe
import win32file
import win32api
import pywintypes

class _PollableReadPipe(_PollableResource):
    implements(IPushProducer)
    def __init__(self, pipe, receivedCallback, lostCallback):
        self.pipe = pipe
        self.receivedCallback = receivedCallback
        self.lostCallback = lostCallback

    def checkWork(self):
        finished = 0
        fullDataRead = []

        while 1:
            try:
                buffer, bytesToRead, result = win32pipe.PeekNamedPipe(self.pipe, 1)
                # finished = (result == -1)
                if not bytesToRead:
                    break
                hr, data = win32file.ReadFile(self.pipe, bytesToRead, None)
                fullDataRead.append(data)
            except win32api.error:
                finished = 1
                break

        dataBuf = ''.join(fullDataRead)
        if dataBuf:
            self.receivedCallback(dataBuf)
        if finished:
            self.cleanup()
        return len(dataBuf)

    def cleanup(self):
        self.deactivate()
        self.lostCallback()

    def close(self):
        try:
            win32api.CloseHandle(self.pipe)
        except pywintypes.error:
            pass

    def stopProducing(self):
        self.close()

    def pauseProducing(self):
        self.deactivate()

    def resumeProducing(self):
        self.activate()

FULL_BUFFER_SIZE = 64 * 1024

class _PollableWritePipe(_PollableResource):
    implements(IConsumer)
    def __init__(self, writePipe, lostCallback):
        self.disconnecting = False
        self.producer = None
        self.producerPaused = 0
        self.streamingProducer = 0
        self.outQueue = []
        self.writePipe = writePipe
        self.lostCallback = lostCallback
        try:
            win32pipe.SetNamedPipeHandleState(writePipe,
                                              win32pipe.PIPE_NOWAIT,
                                              None,
                                              None)
        except pywintypes.error:
            pass

    def close(self):
        self.disconnecting = True

    def bufferFull(self):
        if self.producer is not None:
            self.producerPaused = 1
            self.producer.pauseProducing()

    def bufferEmpty(self):
        if self.producer is not None and ((not self.streamingProducer) or
                                          self.producerPaused):
            self.producer.producerPaused = 0
            self.producer.resumeProducing()
            return True
        return False

    def registerProducer(self, producer, streaming):
        if self.producer is not None:
            raise RuntimeError(
                "Cannot register producer %s, because producer %s was never "
                "unregistered." % (producer, self.producer))
        if not self.active:
            producer.stopProducing()
        else:
            self.producer = producer
            self.streamingProducer = streaming
            if not streaming:
                producer.resumeProducing()

    def unregisterProducer(self):
        self.producer = None

    def writeConnectionLost(self):
        self.deactivate()
        try:
            win32api.CloseHandle(self.writePipe)
        except pywintypes.error:
            pass
        self.lostCallback()

    def writeSequence(self, seq):
        self.outQueue.extend(seq)

    def write(self, data):
        if self.disconnecting:
            return
        self.outQueue.append(data)
        if sum(map(len, self.outQueue)) > FULL_BUFFER_SIZE:
            self.bufferFull()

    def checkWork(self):
        numBytesWritten = 0
        if not self.outQueue:
            if self.disconnecting:
                self.writeConnectionLost()
                return 0
            try:
                win32file.WriteFile(self.writePipe, '', None)
            except pywintypes.error:
                self.writeConnectionLost()
                return numBytesWritten
        while self.outQueue:
            data = self.outQueue.pop(0)
            errCode = 0
            if isinstance(data, unicode):
                raise TypeError("unicode not allowed")
            try:
                errCode, nBytesWritten = win32file.WriteFile(self.writePipe,
                                                             data, None)
            except win32api.error:
                self.writeConnectionLost()
                break
            else:
                numBytesWritten += nBytesWritten
                if len(data) > nBytesWritten:
                    self.outQueue.insert(0, data[nBytesWritten:])
                    break
        else:
            resumed = self.bufferEmpty()
            if not resumed and self.disconnecting:
                self.writeConnectionLost()
        return numBytesWritten

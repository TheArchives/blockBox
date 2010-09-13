# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
import os
import serial
from serial import PARITY_NONE, PARITY_EVEN, PARITY_ODD
from serial import STOPBITS_ONE, STOPBITS_TWO
from serial import FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS
import win32file, win32event
from twisted.protocols import basic
from twisted.internet import abstract
from twisted.python import log
from serialport import BaseSerialPort

class SerialPort(BaseSerialPort, abstract.FileDescriptor):
    connected = 1

    def __init__(self, protocol, deviceNameOrPortNumber, reactor, 
        baudrate = 9600, bytesize = EIGHTBITS, parity = PARITY_NONE,
        stopbits = STOPBITS_ONE, xonxoff = 0, rtscts = 0):
        self._serial = serial.Serial(deviceNameOrPortNumber, baudrate=baudrate,
                                     bytesize=bytesize, parity=parity,
                                     stopbits=stopbits, timeout=None,
                                     xonxoff=xonxoff, rtscts=rtscts)
        self.flushInput()
        self.flushOutput()
        self.reactor = reactor
        self.protocol = protocol
        self.outQueue = []
        self.closed = 0
        self.closedNotifies = 0
        self.writeInProgress = 0
        
        self.protocol = protocol
        self._overlappedRead = win32file.OVERLAPPED()
        self._overlappedRead.hEvent = win32event.CreateEvent(None, 1, 0, None)
        self._overlappedWrite = win32file.OVERLAPPED()
        self._overlappedWrite.hEvent = win32event.CreateEvent(None, 0, 0, None)
        
        self.reactor.addEvent(self._overlappedRead.hEvent, self, 'serialReadEvent')
        self.reactor.addEvent(self._overlappedWrite.hEvent, self, 'serialWriteEvent')
        self.protocol.makeConnection(self)
        flags, comstat = win32file.ClearCommError(self._serial.hComPort)
        rc, self.read_buf = win32file.ReadFile(self._serial.hComPort,
                                               win32file.AllocateReadBuffer(1),
                                               self._overlappedRead)

    def serialReadEvent(self):
        n = win32file.GetOverlappedResult(self._serial.hComPort, self._overlappedRead, 0)
        if n:
            first = str(self.read_buf[:n])
            flags, comstat = win32file.ClearCommError(self._serial.hComPort)
            if comstat.cbInQue:
                win32event.ResetEvent(self._overlappedRead.hEvent)
                rc, buf = win32file.ReadFile(self._serial.hComPort,
                                             win32file.AllocateReadBuffer(comstat.cbInQue),
                                             self._overlappedRead)
                n = win32file.GetOverlappedResult(self._serial.hComPort, self._overlappedRead, 1)
                self.protocol.dataReceived(first + str(buf[:n]))
            else:
                self.protocol.dataReceived(first)
        win32event.ResetEvent(self._overlappedRead.hEvent)
        rc, self.read_buf = win32file.ReadFile(self._serial.hComPort,
                                               win32file.AllocateReadBuffer(1),
                                               self._overlappedRead)

    def write(self, data):
        if data:
            if self.writeInProgress:
                self.outQueue.append(data)
            else:
                self.writeInProgress = 1
                win32file.WriteFile(self._serial.hComPort, data, self._overlappedWrite)

    def serialWriteEvent(self):
        try:
            dataToWrite = self.outQueue.pop(0)
        except IndexError:
            self.writeInProgress = 0
            return
        else:
            win32file.WriteFile(self._serial.hComPort, dataToWrite, self._overlappedWrite)
    
    def connectionLost(self, reason):
        self.reactor.removeEvent(self._overlappedRead.hEvent)
        self.reactor.removeEvent(self._overlappedWrite.hEvent)
        abstract.FileDescriptor.connectionLost(self, reason)
        self._serial.close()

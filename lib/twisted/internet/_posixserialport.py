# Copyright (c) 2001-2007 Twisted Matrix Laboratories.
# See LICENSE for details.
import os, errno
import serial
from serial import PARITY_NONE, PARITY_EVEN, PARITY_ODD
from serial import STOPBITS_ONE, STOPBITS_TWO
from serial import FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS
from serialport import BaseSerialPort
from twisted.internet import abstract, fdesc, main

class SerialPort(BaseSerialPort, abstract.FileDescriptor):
    connected = 1

    def __init__(self, protocol, deviceNameOrPortNumber, reactor, 
        baudrate = 9600, bytesize = EIGHTBITS, parity = PARITY_NONE,
        stopbits = STOPBITS_ONE, timeout = 0, xonxoff = 0, rtscts = 0):
        abstract.FileDescriptor.__init__(self, reactor)
        self._serial = serial.Serial(deviceNameOrPortNumber, baudrate = baudrate, bytesize = bytesize, parity = parity, stopbits = stopbits, timeout = timeout, xonxoff = xonxoff, rtscts = rtscts)
        self.reactor = reactor
        self.flushInput()
        self.flushOutput()
        self.protocol = protocol
        self.protocol.makeConnection(self)
        self.startReading()

    def fileno(self):
        return self._serial.fd

    def writeSomeData(self, data):
        return fdesc.writeToFD(self.fileno(), data)

    def doRead(self):
        return fdesc.readFromFD(self.fileno(), self.protocol.dataReceived)

    def connectionLost(self, reason):
        abstract.FileDescriptor.connectionLost(self, reason)
        self._serial.close()

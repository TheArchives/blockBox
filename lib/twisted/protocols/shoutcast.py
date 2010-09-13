# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.twisted.web import http
from twisted import copyright

class ShoutcastClient(http.HTTPClient):
    userAgent = "Twisted Shoutcast client " + copyright.version

    def __init__(self, path="/"):
        self.path = path
        self.got_metadata = False
        self.metaint = None
        self.metamode = "mp3"
        self.databuffer = ""
        
    def connectionMade(self):
        self.sendCommand("GET", self.path)
        self.sendHeader("User-Agent", self.userAgent)
        self.sendHeader("Icy-MetaData", "1")
        self.endHeaders()
        
    def lineReceived(self, line):
        if not self.firstLine and line:
            if len(line.split(": ", 1)) == 1:
                line = line.replace(":", ": ", 1)
        http.HTTPClient.lineReceived(self, line)
    
    def handleHeader(self, key, value):
        if key.lower() == 'icy-metaint':
            self.metaint = int(value)
            self.got_metadata = True

    def handleEndHeaders(self):
        if self.got_metadata:
            self.handleResponsePart = self.handleResponsePart_with_metadata
        else:
            self.handleResponsePart = self.gotMP3Data

    def handleResponsePart_with_metadata(self, data):
        self.databuffer += data
        while self.databuffer:
            stop = getattr(self, "handle_%s" % self.metamode)()
            if stop:
                return

    def handle_length(self):
        self.remaining = ord(self.databuffer[0]) * 16
        self.databuffer = self.databuffer[1:]
        self.metamode = "meta"
    
    def handle_mp3(self):
        if len(self.databuffer) > self.metaint:
            self.gotMP3Data(self.databuffer[:self.metaint])
            self.databuffer = self.databuffer[self.metaint:]
            self.metamode = "length"
        else:
            return 1
    
    def handle_meta(self):
        if len(self.databuffer) >= self.remaining:
            if self.remaining:
                data = self.databuffer[:self.remaining]
                self.gotMetaData(self.parseMetadata(data))
            self.databuffer = self.databuffer[self.remaining:]
            self.metamode = "mp3"
        else:
            return 1

    def parseMetadata(self, data):
        meta = []
        for chunk in data.split(';'):
            chunk = chunk.strip().replace("\x00", "")
            if not chunk:
                continue
            key, value = chunk.split('=', 1)
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            meta.append((key, value))
        return meta
    
    def gotMetaData(self, metadata):
        raise NotImplementedError, "implement in subclass"
    
    def gotMP3Data(self, data):
        raise NotImplementedError, "implement in subclass"

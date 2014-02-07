#!/usr/bin/env python
# Packtizer.py - Message Packetizer
# As per https://docs.google.com/document/d/1fwUtzFUhTzwjHrbfUayRG5sM_3TzdPlPgWjwXnY8fsU/edit
#
# Copyright 2014 Mark Jessop <mark.jessop@adelaide.edu.au>
# 
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

import crc16,struct
import numpy as np

class Packetizer(object):
    """ Message Packetizer Class """
    def __init__(self, sync_bytes = '\xAB\xCD', crc32 = False):

        self.crc32_enabled = crc32
        self.sync_bytes = sync_bytes
        self.messages = []

    def pack_message(self, msg):
        if(len(msg)>1023):
            msg = msg[:1023]  # TODO: Split up messages nicely? Do we care?
            
        packet_length = len(msg) & 1023 # Packet Flags & Header

        # TODO: Nicer way of handling bitfields for the packet flags
        if(self.crc32_enabled):
            packet_length = packet_length | 0x8000 # Set the CRC32 flag bit.
            crc = struct.pack(">L",0xFFFF) # TODO: crc32 from python libraries?
        else:
            crc = struct.pack(">H", crc16.crc16_buff(struct.pack(">H", packet_length) + msg))

        # Construct the packet
        packet = self.sync_bytes + struct.pack(">H", packet_length) + msg + crc

        self.messages.append(packet)

        return packet

# Test script.
if __name__ == "__main__":
    p = Packetizer()
    packet = p.pack_message("Hello")
    print packet
    print np.fromstring(packet,dtype=np.uint8)




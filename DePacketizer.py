#!/usr/bin/env python
# DePacktizer.py - Message DePacketizer
# As per https://docs.google.com/document/d/1fwUtzFUhTzwjHrbfUayRG5sM_3TzdPlPgWjwXnY8fsU/edit
#
# Absorbs bits (numpy arrays, strings, whatever), and emits packets, if found.
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

import struct, crc16, logging, sys
import numpy as np


class DePacketizer(object):
    """ Message DePacketizer Class """
    def __init__(self, sync_bytes = '\xAB\xCD', payload_length_cap = 32, callback = False):
        self.sync_bytes = sync_bytes
        self.sync_length = len(sync_bytes) * 8
        self.payload_length_cap = payload_length_cap
        self.callback = callback

        self.buffer_state = "APPEND" # "APPEND", while waiting for enough bits to attempt to extract a full packet, 
                                     # "SHIFT", for when we have reached our maximum buffer size, and can just clock through bits. 
        self.state = "NEED_MORE_DATA"
        self.buffer = np.array([]).astype(np.uint8)

    # Test buffer for sync bytes. If found, check for the rest of the packet, if enough bits are available. 
    def test_buffer(self):
        if len(self.buffer)> self.sync_length + 16: # Allow for different sync lengths.
            # Convert the first X bits to a string, and test against the sync bytes.
            buffer_head = np.packbits(self.buffer[0:self.sync_length]).tostring()

            if buffer_head == self.sync_bytes: # Maybe we have something?

                # Extract the packet flags and payload length.
                packet_flags = np.packbits(self.buffer[self.sync_length:self.sync_length+16]).tostring()
                packet_flags = struct.unpack(">H", packet_flags)[0]
                packet_length = packet_flags & 0x03FF # Extract just the packet length

                if(packet_length > self.payload_length_cap):
                    # Payload is bigger than our cap.
                    # At this point we assume the data is corrupt, and continue clocking through bits.
                    logging.debug("Packet length bigger than cap.")
                    return

                # Get the CRC type and length from the MSB of the packet flags.
                crc_type = "CRC32" if (packet_flags & 0x8000 == 1) else "CRC16"
                crc_length = 4 if crc_type == "CRC32" else 2

                # Check we have enough bits to test the entire packet.
                if(len(self.buffer) >= self.sync_length + 16 + packet_length*8 + crc_length*8):
                    # Convert the bit array to a string
                    packet_string = np.packbits(self.buffer[0:(self.sync_length + 16 + packet_length*8 + crc_length*8)]).tostring()
                    logging.debug("Possible Packet: " + packet_string)
                    logging.debug(str(np.packbits(self.buffer[0:(self.sync_length + 16 + packet_length*8 + crc_length*8)])))
                    # Extract CRC, and calc CRC
                    if crc_type == "CRC16":
                        calc_crc = crc16.crc16_buff(packet_string[len(self.sync_bytes):-2])
                        packet_crc = struct.unpack(">H",packet_string[-2:])[0]
                    else:
                        calc_crc = 0xFFFF
                        packet_crc = struct.unpack(">L", packet_string[-4:])[0]

                    logging.debug("Packet CRC: " + str(packet_crc) + " Calc CRC: "+ str(calc_crc))

                    # Test CRC
                    if packet_crc == calc_crc:
                        # Woohoo! We have a packet!
                        payload = packet_string[len(self.sync_bytes)+2:-2]

                        logging.info("Found complete packet: " + payload)
                        # Do somethign with the packet
                        if self.callback != False:
                            self.callback(payload)
                        # Clear the packet bits out of the buffer.
                        self.buffer_state = "SHIFT"
                        # TODO
                    else:
                        # Packet failed CRC. Continue clocking through bits in case this was a false positive.
                        logging.debug("CRC Check failed. False positive on sync?")
                        self.buffer_state = "SHIFT"
                        return
                else:
                    # We need more bits. Make sure new bits are appended, so we don't shift out our sync header.
                    self.buffer_state = "APPEND"
                    return
            else:
                # No sync header match. Continue clocking bits through.
                self.buffer_state = "SHIFT"
                return
        else:
            # We need more bits to check the sync header.
            self.buffer_state = "APPEND"
            return

    def process_bit(self,bit):
        # This function only takes np.uint8's
        if type(bit) != np.uint8:
            bit = np.uint8(bit)
        if bit != 0 and bit != 1:  # This should never happen, but anyway... 
            return

        # Now either append the bit to the buffer, or rotate the buffer left and add the bit to the end.
        if self.buffer_state == "SHIFT":
            self.buffer = np.roll(self.buffer,-1)
            self.buffer[-1] = bit
        elif self.buffer_state == "APPEND":
            self.buffer = np.append(self.buffer, bit)

            if len(self.buffer) == (self.payload_length_cap * 8 + 64):  # If the buffer has reached the maximum size, switch to the "SHIFT" state.
                logging.debug("Buffer full, now shifting data in.")
                self.buffer_state = "SHIFT"

        # Test the buffer for validity
        self.test_buffer()

    def process_data(self,data):
        # Convert incoming data, whatever it is, to a numpy array of uint8's
        if type(data) == np.ndarray:
            data = data.astype(np.uint8)
        elif type(data) == str:
            data = np.unpackbits(np.fromstring(data ,dtype=np.uint8))
        else:
            return
        
        logging.debug("Incoming Data: " + str(data))

        for bit in data:
            self.process_bit(bit)

# Test script.
if __name__ == "__main__":
    # Set up logging to stdout instead of a file.
    root = logging.getLogger()
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    root.addHandler(ch)
    root.setLevel(logging.DEBUG)

    # Callback function. This is where you'd pass packts onto Habitat or whatever.
    def print_payload(payload):
        print payload

    # Generate some packets, and intersperse random data between them.
    import Packetizer as p
    import random,string
    p = p.Packetizer()

    data = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    data = data + p.pack_message("testing")
    data2 = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(16))
    data2 = data2 + p.pack_message("testing again")

    # Pass data through the DePacketizer
    dp = DePacketizer(callback=print_payload)
    dp.process_data(data)
    dp.process_data(data2)
        
#!/usr/bin/env python
# demod_test.py - Attempt to extract packet data from a wave file.
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

import numpy as np
import MFSKDemodulator, DePacketizer, MFSKSymbolDecoder, time, logging, sys
from scipy.io import wavfile

# Callback for when a complete packet is recovered.
def print_payload(payload):
    print "\n"
    print payload

# I should probably be doing this using the functions in ModemUtils.
symb_dec = MFSKSymbolDecoder.MFSKSymbolDecoder(num_tones=16, gray_coded=True)

# De-Packetizer
packet_extract = DePacketizer.DePacketizer(callback=print_payload)

# Callback for when a symbol is recovered.
def parse_symbol(tone):
    tone_bits = symb_dec.tone_to_bits(tone['symbol'])
    packet_extract.process_data(tone_bits)

demod = MFSKDemodulator.MFSKDemodulator(callback=parse_symbol)

# Set up logging so that we see all debug information from the demod.
root = logging.getLogger()
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
root.addHandler(ch)
root.setLevel(logging.DEBUG)

# Read in a wave file containing MFSK packets. This can be generated using 'gen_test_packets.py'
fs, data = wavfile.read('generated_MFSK16_packets.wav')

# Convert to float
if(data.dtype == np.int16):
    data = data.astype(np.float)/2**16
elif(data.dtype == np.int32):
    data = data.astype(np.float)/2**32

# Feed the demod the entire file.
demod.consume(data)

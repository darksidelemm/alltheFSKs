#!/usr/bin/env python
# gen_test_packets.py
#
# Copyright 2013 Mark Jessop <mark.jessop@adelaide.edu.au>
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
import MFSKModulator
import ConvEncoder
import Packetizer


# MFSK16 Compatible waveform.
symbol_rate = 15.625
base_freq = 1500
bits_per_symbol = 4

preamble_tones = [0,15,0,15,0,15,0,15,0,15,0,15,0,15,0,15,0,15,0,15,0,15,0,15,0,15,0,15,0,15]
payload_list = ["Testing", "DE VK5QI", "More Testing"]

mod = MFSKModulator.MFSKModulator(symbol_rate = symbol_rate, tone_spacing = symbol_rate, start_silence=5, base_freq=base_freq)

p = Packetizer.Packetizer()

# Modulate a preamble (How long does the MFSK demod take to get symbol sync?)
mod.modulate_symbol(preamble_tones)

data = ""
for payload in payload_list:
    data = data + p.pack_message(payload)

print data

tx_bits = np.unpackbits(np.fromstring(data, dtype=np.uint8))
print str(tx_bits)

mod.modulate_bits(bits_per_symbol,tx_bits)


# Write modulated signal to file.
mod.write_wave('generated_MFSK16_packets.wav')



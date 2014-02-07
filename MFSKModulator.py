#!/usr/bin/env python
# MFSKModulator.py - Constant Amplitude, Continuous Phase MFSK Modulator Class
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

from pylab import *
import numpy as np
from scipy.io import wavfile
from ModemUtils import *


class MFSKModulator(object):
    """ Constant Amplitude/Phase MFSK Modulator Class """
    def __init__(self, sample_rate=8000, base_freq=1000, symbol_rate=31.25, tone_spacing=31.25, start_silence=0, amplitude=0.5):
        self.sample_rate = sample_rate
        self.base_freq = base_freq
        self.symbol_rate = symbol_rate
        self.tone_spacing = tone_spacing
        self.symbol_length = int(sample_rate/symbol_rate)
        self.amplitude = amplitude

        self.phase = int(0)
        self.baseband = np.zeros(start_silence*self.symbol_length)

        self.read_ptr = 0
        self.write_lock = 0

    def read(self,block_size):
        self.write_lock = 1

        samples_available = len(self.baseband) - self.read_ptr
        if(block_size > samples_available):
            # Add silence to baseband output, so we can give data to the consumer
            self.baseband = np.append(self.baseband, np.zeros(block_size - samples_available))

        self.write_lock = 0
        chunk = self.baseband[self.read_ptr:(self.read_ptr + block_size)]
        self.read_ptr = self.read_ptr + block_size

        return chunk

    def write(self, data):
        # In case we have concurrency issues
        while (self.write_lock==1):
            pass

        # Append data onto the end of our baseband array.
        self.baseband = np.append(self.baseband,data)

    def emit_all(self):
        return self.baseband

    def write_wave(self,filename):
        scaled = np.int16(self.baseband * 32767)
        wavfile.write(filename,self.sample_rate,scaled)

    def modulate_symbol(self,symbol_list=0):
        for symb in symbol_list:
            tone_freq = float(self.base_freq) + float(self.tone_spacing)*int(symb)
            x = np.arange(self.phase, self.phase + self.symbol_length, 1)
            symbol = self.amplitude * np.cos(2*np.pi*(tone_freq/self.sample_rate)*x)

            self.write(symbol)

    def modulate_bits(self, symbol_bits, bit_array):
        """ Converts a numpy array of bits (0,1) to gray coded symbols, then transmits them. 
        The array length must be a multiple of the symbol bits.
        """

        # Pad array out to a multiple of symbol_bits
        if(len(bit_array)%symbol_bits > 0):
            bit_array = np.append(bit_array,np.zeros(symbol_bits - len(bit_array)%symbol_bits))

        bit_array = np.reshape(bit_array,(-1,symbol_bits)).astype(np.int8)

        symb_array = []

        for symb in bit_array:
            # Convert array bits to an integer.
            print "Symb: " + str(symb)
            symb_int = symb.dot(1 << np.arange(symb.shape[-1] - 1, -1, -1))
            print "SymbInt:" + str(symb_int)
            symb_int = gray_encode(symb_int) # Gray Coding.
            print "SymbGray:" + str(symb_int)
            symb_array.append(symb_int)

        self.modulate_symbol(symb_array)
        print str(symb_array)
        return symb_array

# Test script.
if __name__ == "__main__":
    # Instantiate a Thor8 Compatible modulator
    #mod = MFSKModulator(symbol_rate = 7.8125, tone_spacing = 7.8125*2, start_silence=5, base_freq=1500)

    # MFSK16 Modulator
    mod = MFSKModulator(symbol_rate = 15.625, tone_spacing = 15.625, start_silence=0, base_freq=1500)

    # "CQ CQ CQ DE VK5QI VK5QI"
    #thorcq = [2,4,6,8,10,12,14,16,0,2,4,6,8,10,12,14,6,8,0,2,12,4,6,8,0,10,16,12,8,4,6,12,4,10,16,8,12,14,2,12,2,6,2,12,8,6,2,15,5,11,16,6,15,9,4,17,5,0,5,12,14,17,3,16,12,7,12,7,11,17,2,5,9,4,0,10,14,1,13,1,12,15,1,13,9,11,5,14,0,10,17,2,14,0,6,2,0,7,9,7,4,3,5,17,13,5,13,6,9,12,4,12,2,10,16,10,3,14,1,12,0,8,6,12,14,6,1,6,8,13,9,5,10,7,9,13,9,16,3,16,1,7,6,5,14,16,14,13,11,14,8,14,16,6,17,2,5,16,14,12,10,2,14,3,10,15,4,10,4,16,8,16,10,15,4,6,9,13,7,4,17,3,16,2,8,11,14,0,13,9,1,5,10,4,10,3,6,10,4,0,2,14,5,9,1,8,11,5,9,15,11,9,16,0,16,13,12,14,8,4,14,4,15,0,3,13,3,11,1,7,1,12,5,10,3,9,17,15,3,5,15,10,15,17,4,0,14,1,16,0,4,0,7,12,7,10,16,15,14,5,7,5,4,2,5,17,13,15,5,8,1,12,5,13,3,1,7,5,2,5,0,3,9,13,7,13,15,9,2,17,3,14,6,4,13,8,4,12,14,6,14,1,10,5,8,1,7,2,0,11,3,5,12,10,2,11,8,12,9,7,1,13,0,7,1]
    #mod.modulate_symbol(thorcq)
    #mod.write_wave("thor8_test.wav")

    #thortones = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]
    #mod.modulate_symbol(thortones)
    #mod.write_wave("thor8_sweep.wav")

    #thortones = [0,2,4,6,8,10,12,14,16,1,3,5,7,9,11,13,15,17,0,2,4,6,8,10,12,14,16,1,3,5,7,9,11,13,15,17,0,2,4,6,8,10,12,14,16,1,3,5,7,9,11,13,15,17,0,2,4,6,8,10,12,14,16,1,3,5,7,9,11,13,15,17,0,2,4,6,8,10,12,14,16,1,3,5,7,9,11,13,15,17,0,2,4,6,8,10,12,14,16,1,3,5,7,9,11,13,15,17]
    #mod.modulate_symbol(thortones)
    #mod.write_wave("thor8_sweep_1500.wav")

    #mfsk_tones = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
    #mod.modulate_symbol(mfsk_tones)
    #mod.write_wave("mfsk16_sweep_1500.wav")

    file_length = 512 # symbols
    symbols = (np.arange(0,file_length)*3)%16 # Step 3 tones at a time.
    mod.modulate_symbol(symbols)
    mod.write_wave("mfsk16_3stepped_1500.wav")


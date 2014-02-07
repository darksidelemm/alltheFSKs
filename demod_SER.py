#!/usr/bin/env python
# demod_SER.py - Some analysis of symbol timing and symbol detection error.
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
import MFSKDemodulator, DePacketizer, MFSKSymbolDecoder, time, MFSKModulator, sys
from scipy.io import wavfile

base_freq = 1500
symbol_rate = 15.625
num_tones = 16
sample_rate = 8000
amplitude = 0.5

# How many symbols to pass through the demodulator?
num_tests = 500
max_errors = 100

ebno_range = np.arange(-10,20,1)
ebno_range = np.array([10])


symbol_length = sample_rate / symbol_rate

# We need to declare these here so parse_symbol can access them.
n = 0
errors = 0

# A function to handle data discovered by the Demodulator class.
def parse_symbol(data):
    global n,errors

    symbol = data["symbol"]
    sample = data["sample"]
    s2n = data["s2n"]

    #symbol_number = int(round(sample/float(expected_symbol_timing)))
    timing_error = sample - int(symbol_length * round(sample/float(symbol_length)))

    expected_symbol = ((n)*3)%num_tones

    #print "N=%d, Expected=%d, Decoded=%d, Timing error=%d, SNR=%d" % (n, expected_symbol , symbol, timing_error, s2n)
    
    if(symbol != expected_symbol):
        errors += 1
        #print "Symbol Error. errors = %d" % (errors)
        print "x",
    else:
        print ".",

    sys.stdout.flush()

output = []

for ebno in ebno_range:
    # Re-instantiate the modulator and demodulator objects
    mod = MFSKModulator.MFSKModulator(symbol_rate= symbol_rate, tone_spacing = symbol_rate, start_silence=0, base_freq=base_freq, sample_rate=sample_rate, amplitude=amplitude)
    demod = MFSKDemodulator.MFSKDemodulator(sample_rate=sample_rate, base_freq=base_freq, symbol_rate=symbol_rate, num_tones = num_tones, callback=parse_symbol)

    # Calculate the required noise power
    noise_power = (1/(10**(float(ebno)/10))) * (amplitude**2 * (1/symbol_rate) * (num_tones * symbol_rate))/(2*np.log2(num_tones))

    n = 0
    errors = 0

    # Generate and process symbols until we hit our endpoint
    while n<num_tests and errors<max_errors:
        mod.modulate_symbol([ (n*3)%num_tones ])
        symbol = mod.baseband[-1*symbol_length:]

        noise = np.sqrt( (noise_power/( 2*num_tones * symbol_rate))) * np.random.randn(len(symbol))

        data = symbol + noise
        demod.consume(data)
        n += 1


    #print str(noise_power) + "," + str(np.max( np.sqrt( (noise_power/( 2*num_tones * symbol_rate))) * np.random.randn(512)))
    print "\nEb/No %d dB:  SER: %.4f" % (ebno, float(errors)/(n-1))
    output.append([float(ebno), float(errors)/(n-1)])


print output
#demod.consume(data)


#[[-10.0, 0.33222591362126247], [-9.0, 0.36101083032490977], [-8.0, 0.352112676056338], [-7.0, 0.34965034965034963], [-6.0, 0.2994011976047904], [-5.0, 0.33783783783783783], [-4.0, 0.273972602739726], [-3.0, 0.22624434389140272], [-2.0, 0.2242152466367713], [-1.0, 0.19839679358717435], [0.0, 0.1523046092184369], [1.0, 0.156312625250501], [2.0, 0.09018036072144289], [3.0, 0.09218436873747494], [4.0, 0.06613226452905811], [5.0, 0.03807615230460922], [6.0, 0.014028056112224449], [7.0, 0.01603206412825651], [8.0, 0.006012024048096192], [9.0, 0.006012024048096192], [10.0, 0.0], [11.0, 0.0], [12.0, 0.0], [13.0, 0.0], [14.0, 0.0], [15.0, 0.0], [16.0, 0.0], [17.0, 0.0], [18.0, 0.0], [19.0, 0.0]]

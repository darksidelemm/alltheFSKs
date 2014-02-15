#!/usr/bin/env python
# demod_BER.py - Calculate BER vs Eb/No for a range of Eb/No values.
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
from pylab import *
import MFSKDemodulator, DePacketizer, MFSKSymbolDecoder, time, MFSKModulator, sys, logging
from scipy.io import wavfile

base_freq = 1500
sample_rate = 8000
amplitude = 0.5

cheat_symbol_detect = True

# 16-FSK, 15.625 baud.
symbol_rate = 15.625
num_tones = 16
tone_bits = int(np.log2(num_tones))

# 64-FSK, 15.625 baud.
# symbol_rate = 15.625
# num_tones = 64
# tone_bits = 6

# 32-FSK, 31.25 baud
# symbol_rate = 31.25
# num_tones = 32
# tone_bits = 8

# How many symbols to pass through the demodulator?
num_tests = 4000
max_errors = 400

ebno_range = np.arange(-10,30,1)
#ebno_range = np.array([5])


symbol_length = sample_rate / symbol_rate

# We need to declare these here so parse_symbol can access them.
n = 0
bits = 0
errors = 0
symb_dec = MFSKSymbolDecoder.MFSKSymbolDecoder(num_tones=num_tones, gray_coded=True)

# Enable debug output from the demod.
# root = logging.getLogger()
# ch = logging.StreamHandler(sys.stdout)
# ch.setLevel(logging.DEBUG)
# root.addHandler(ch)
# root.setLevel(logging.DEBUG)

# A function to handle data discovered by the Demodulator class.
def parse_symbol(data):
    global n,errors

    symbol = data["symbol"]
    sample = data["sample"]
    s2n = data["s2n"]
    timing = data["timing"]



    #symbol_number = int(round(sample/float(expected_symbol_timing)))
    timing_error = sample - int(symbol_length * round(sample/float(symbol_length)))

    if cheat_symbol_detect:
        expected_symbol = (((n-1))*3)%num_tones
    else:
        expected_symbol = (((n))*3)%num_tones
    expected_bits = symb_dec.tone_to_bits(expected_symbol)

    #print "N=%d, Expected=%d, Decoded=%d, Timing error=%d, SNR=%d" % (n, expected_symbol , symbol, timing_error, s2n)


    actual_bits = symb_dec.tone_to_bits(symbol)
    bit_errors = np.sum(np.bitwise_xor(expected_bits, actual_bits))
    errors += bit_errors

    error_string = ""

    if bit_errors>0:
        error_string = "x"*int(bit_errors)
    else:
        error_string = "."*tone_bits

    #print "[%s %d %d %s]" % (timing, timing_error, symbol, error_string) ,
    print error_string ,

    sys.stdout.flush()

output = []

for ebno in ebno_range:
    # Re-instantiate the modulator and demodulator objects
    mod = MFSKModulator.MFSKModulator(symbol_rate= symbol_rate, tone_spacing = symbol_rate, start_silence=0, base_freq=base_freq, sample_rate=sample_rate, amplitude=amplitude)
    demod = MFSKDemodulator.MFSKDemodulator(sample_rate=sample_rate, base_freq=base_freq, symbol_rate=symbol_rate, num_tones = num_tones, callback=parse_symbol, cheating = cheat_symbol_detect)

    signal_log = np.array([])
    noise_log = np.array([])

    # Calculate the required noise variance
    variance = (amplitude**2 / 2) * sample_rate / (symbol_rate * 10**(float(ebno)/10) * np.log2(num_tones))
    #variance = 1/10**(ebno/10.0) * (amplitude**2 / 2.0) * symbol_length/float(sample_rate) * (1/np.log2(num_tones))

    n = 0
    errors = 0
    bits = 0

    print "Running tests for %d dB Eb/No:" % (ebno)

    # Generate and process symbols until we hit our endpoint
    while bits<num_tests and errors<max_errors:
        mod.modulate_symbol([ (n*3)%num_tones ])
        symbol = mod.baseband[-1*symbol_length:]

        # Generate the noise.
        noise = np.sqrt(variance) * np.random.randn(len(symbol))

        signal_log = np.append(signal_log,symbol)
        noise_log = np.append(noise_log,noise)

        data = symbol + noise
        demod.consume(data)
        n += 1
        bits += tone_bits

        # Reset the counters after 20 bits, to reduce the effect of start-up errors.
        if n==20:
            errors = 0
            bits = 0


    #print str(noise_power) + "," + str(np.max( np.sqrt( (noise_power/( 2*num_tones * symbol_rate))) * np.random.randn(512)))
    print "\nEb/No %d dB:  BER: %.4f" % (ebno, float(errors)/(bits))
    output.append([float(ebno), float(errors)/(bits)])

    print ("C %f N %f Es %f No %f Es/No %f dB Eb/No %f dB") % (np.var(signal_log), np.var(noise_log), np.var(signal_log)/symbol_rate, np.var(noise_log)/sample_rate, 10*np.log10((np.var(signal_log)/symbol_rate)/(np.var(noise_log)/sample_rate)), 10*np.log10((np.var(signal_log)/symbol_rate)/(tone_bits*np.var(noise_log)/sample_rate)))

    #plot(8000.0*np.fft.fftfreq(len(noise_log)),20*np.log10(np.absolute(np.fft.fft(noise_log+signal_log))))
    #show()

for line in output:
    print "%d, %.4f" % (line[0], line[1])
# Save output to a file for further analysis
#np.save('baseband', signal_log + noise_log)


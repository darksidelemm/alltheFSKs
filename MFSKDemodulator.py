#!/usr/bin/env python
# MFSKDemodulator.py - MFSK Demodulator
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

from pylab import *
import numpy as np
from scipy.io import wavfile
from scipy.signal import hilbert
from ModemUtils import *
import logging

class MFSKDemodulator(object):
    """ MFSK Demodulator Class 

    sample_rate:    Sample rate of incoming data (Hz)
    base_freq:      The frequncy of the lowest MFSK tone (Hz)
    symbol_rate:    Symbol rate of the MFSK modulation (baud)
    num_tones:      Number of tones in use. Tone spacing is assumed to be orthogonal (equal to the symbol rate).
    callback:       Function pointer. A dictionary containing symbol information is passed to this function when
                    a symbol is detected.

    """
    def __init__(self, sample_rate=8000, base_freq=1500, symbol_rate=15.625, num_tones = 16, callback = False, gray_coded = True, cheating = False):
        self.fs = sample_rate
        self.base_freq = base_freq
        self.symbol_rate = symbol_rate
        self.tone_spacing = symbol_rate
        self.num_tones = num_tones
        self.callback = callback
        self.gray_coded = gray_coded

        # Cheating mode! Ignore timing estimation and demodulate whenever n is a multiple of the symbol length
        self.cheating = cheating

        #
        self.buffer_size = 4 # Length of the internal buffers used, in symbols.
        self.block_length = 16 # How many samples to process at a time. Higher values will increase speed, but reduce accuracy.
        self.dft_phase_threshold = 0.01
        self.mixing_phase = 0 # So we can mix with constant phase.
        self.sample_count = 0 # Internal counter for testing

        # Calculate some variables we need.
        self.sym_bits = int(np.log2(self.num_tones))
        self.symbol_length = int(round(self.fs/self.symbol_rate))
        # Calculate how far we need to move the signal to align it over a FFT bin (usually not far)
        self.mixing_freq = round(self.base_freq/self.symbol_rate)*self.symbol_rate - self.base_freq
        # Location of 'tone zero' in the symbol-length FFT.
        self.tone_zero = int(round(self.base_freq/self.symbol_rate))

        # Instantiate our local buffers.
        self.sample_buffer = np.zeros( self.symbol_length*self.buffer_size, dtype=np.complex )
        self.fft_energy_buffer = np.zeros( (self.num_tones,self.symbol_length*self.buffer_size), dtype=np.complex )
        self.max_fft_energy_buffer = np.zeros( self.symbol_length*self.buffer_size, dtype=np.float )

        # Symbol storage, for SNR calculations.
        self.symbol_gap = 0
        self.currsymbol = 0
        self.last_symbol = 0
        self.last_symbol2 = 0
        self.s2n = 0
        self.s2n_instant = 0
        self.last_dftphase = 0.0

        # and some debugging buffers
        self.dft_phase = np.array([])


    def consume(self,data):
        """
        Consumes incoming data samples, mixes such that the data aligns over a FFT bin then passes it onto the symbol tracker.

        data: Numpy float array. Preferably 2^n samples long, but doesn't matter so much.
        """

        # Type checking

        # Hilbert transform to get the analytic (single-sided) signal.
        # We don't actually need to do this.
        #data = hilbert(data)

        # Mix the signal so that it lines up with a FFT bin.
        data = data*hilbert(np.cos(2.0*np.pi*(self.mixing_freq/self.fs)*np.arange(self.mixing_phase,self.mixing_phase+data.size)))
        self.mixing_phase = self.mixing_phase + len(data)

        # Feed data to symbol_detector, 1 sample at a time.
        # TODO: Make the symbol_detect function process more than on sample at a time.

        #for sample in data:
        #    self.symbol_detect(sample)

        data = np.reshape(data,(-1,self.block_length))

        for block in data:
            self.symbol_detect(block)



    def symbol_detect(self,samples):
        """
        Consumes a sample of data, adding it to a buffer and looking for the beginning of a symbol period.

        """

        # Roll buffers.
        self.sample_buffer = np.roll(self.sample_buffer,-1*self.block_length)
        self.max_fft_energy_buffer = np.roll(self.max_fft_energy_buffer, -1)
        self.fft_energy_buffer = np.roll(self.fft_energy_buffer, -1, axis=1)

        # Add new samples.
        self.sample_buffer[-1*self.block_length:] = samples

        # Calculate FFT over the last (symbol_length) samples in the buffer
        fft_instant = np.fft.fft(self.sample_buffer[-1*self.symbol_length:])

        # Add the relevant bins to a buffer.
        # TODO: Sum positive and negative frequency bins! Might add 3dB
        self.fft_energy_buffer[:,-1] = fft_instant[self.tone_zero:self.tone_zero+self.num_tones]
        # Add the maximum bin to the end of another buffer for signal energy detection.
        self.max_fft_energy_buffer[-1] = np.max(np.absolute(self.fft_energy_buffer[:,-1]))

        # Calculate single-point DFT phase at (symbol_rate) Hz over the max fft energy buffer.
        # If block_length is >1, the fft energy data is effectively downsampled by that factor, and we
        # compensate for that here
        dft_energy = np.angle( self.max_fft_energy_buffer.dot(np.exp(-2*np.pi*1j * (self.symbol_rate/(self.fs/self.block_length)) * np.arange(0,len(self.max_fft_energy_buffer))))) % (2*np.pi)
        # Save the dft phase value for debugging purposes
        self.dft_phase = np.append(self.dft_phase, dft_energy)

        # SYMBOL DETECTION

        # Cheating mode: assume symbols start at sample 0, and have perfect timing.
        # Useful for 'ideal' performance tests.
        if self.cheating:
            if self.sample_count%self.symbol_length == 0:
                logging.debug("Cheating..")
                self.detect_symbol("C")
        else:
            # Zero crossing symbol detection: Detect the zero crossing of the DFT phase. 
            # This indicates that the last (symbol_length) symbols in the buffer contain a symbol.
            if(dft_energy<1.0 and self.last_dftphase > 5.5 and self.symbol_gap > (self.symbol_length*0.8)):
                self.detect_symbol("D")

            # Flywheeling: Attempt to detect a symbol when no zero crossing are detected in the last
            # (symbol_length) samples.
            if self.symbol_gap > self.symbol_length:
                logging.debug("Flywheeling...")
                self.detect_symbol("F")

        # Increment counters.
        self.symbol_gap += self.block_length
        self.sample_count = self.sample_count + self.block_length
        self.last_dftphase = dft_energy

    def detect_symbol(self, timing):
        """
        Run the symbol detection routines, and pass decoded data to the callback function.
        """
        self.hard_decode()
        self.eval_s2n()

        self.symbol_gap = 0

        symbol_stats = {"symbol":self.currsymbol, "sample":self.sample_count, "s2n":(20*np.log10(self.s2n)), "s2n_instant":(20*np.log10(self.s2n_instant)), "timing":timing}
        logging.debug(str(symbol_stats))
        if self.callback != False:
            self.callback(symbol_stats)

    def hard_decode(self):
        """
        Attempt to to hard symbol decoding on the most recent entry in the FFT energy buffer.
        """

        self.currsymbol = np.argmax(np.absolute(self.fft_energy_buffer[:,-1]))

        # Mixing causes the spectrum to be flipped, so our symbol output also needs to be flipped
        # TODO: Fix this. We shouldn't need to mix the received signal so far. It only has to be mixed so the tones align to
        # integer multiples of the symbol rate.
        #self.currsymbol = self.num_tones - self.currsymbol - 1

        self.last_symbol2 = self.last_symbol
        self.last_symbol = self.currsymbol

        return self.currsymbol#gray_decode(symbol)


    def decayavg(self, average, input, weight):
        """ 
        Decaying average, ported from fldigi.
        """
        if (weight <= 1.0):
            return input;
        else:
            return input * (1.0/weight) + average * (1.0 - (1.0/weight))

    def eval_s2n(self):
        """
        SNR Estimation, using FFT bin magnitudes. Ported from fldigi.
        """
        sig = np.absolute(self.fft_energy_buffer[:,-1][self.currsymbol])
        noise = np.absolute(self.fft_energy_buffer[:,-1][self.last_symbol2]) * (self.num_tones)
        if(noise>0):
            self.s2n = self.decayavg(self.s2n, sig/noise, 16)
            self.s2n_instant = sig/noise

    def soft_decode(self):
        """
        Port of fldigi's mfsk::softdecode function to numpy.
        Produces log-likleyhoods for each bit.
        """
        b = np.zeros(self.sym_bits, dtype=float)

        # Iterate over the symbol bins.
        for i in range(0,self.num_tones):
            if self.gray_coded:
                j = gray_decode(i)
            else:
                j = i

            # Get the magnitude of this symbol bin.
            binmag = np.absolute(self.fft_energy_buffer[:,-1][i])
            # This produces the bits that a symbol represents, as an array of -1's and 1s. There's probably a more 'pythonic' way of doing this
            symbol_weights = 2*np.unpackbits(np.array([j], dtype=np.uint8)).astype(np.float)[-1*self.sym_bits:] - 1
            # Then we multiply these bits by the magnitude of the symbol bin, and add it to our total.
            b += symbol_weights * binmag

        # Now we normalise the values to +- 1.
        b = b/np.sum(np.absolute(self.fft_energy_buffer[:,-1]))
        return b




# Test script.
if __name__ == "__main__":
    filename = 'generated_MFSK16_packets.wav';

    fs, data = wavfile.read('generated_MFSK16_packets.wav')

    if(data.dtype == np.int16):
        data = data.astype(np.float)/2**16
    elif(data.dtype == np.int32):
        data = data.astype(np.float)/2**32

    demod = MFSKDemodulator(sample_rate = fs)

    root = logging.getLogger()
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    root.addHandler(ch)
    root.setLevel(logging.DEBUG)

    # Feed data in X samples at a time. This kind of simulates getting data from a buffered audio stream.
    chunk_size = 1024
    i = 0
    while (i+chunk_size < len(data)): 
        demod.consume(data[i:i+chunk_size])
        i = i + chunk_size

    # process any remaning data.
    demod.consume(data[i:])







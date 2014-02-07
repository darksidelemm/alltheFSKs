#!/usr/bin/env python
# CCIR493-4.py - CCIR-493-4 HF SELCALL Implementation
#
# Ported from the C implementation in the QITX project.
#
# This implementation is based partly on the CCIR 493-9 specification,
# and partly on reverse engineered SELCALL packets transmitted from a commercial
# HF radio.
#    
# CCIR 493-9 is available here: http://hflink.com/selcall/ITU-R%20M.493-9%20specification.pdf
# I can't find a complete copy of CCIR 493-4 anywhere...
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

import MFSKModulator as mfsk

# Some defines for SELCALL Codes.
SEL_SEL = 120     # Selective call
SEL_ID  = 123     # Individual station semi-automatic/automatic service (Codan channel test)
SEL_EOS = 127     # ROS
SEL_RTN = 100     # Routine call
SEL_ARQ = 117     # Acknowledge Request (EOS)
SEL_PDX = 125     # Phasing DX Position
SEL_PH7 = 111     # Phasing RX-7 position
SEL_PH6 = 110     # RX-6
SEL_PH5 = 109     # RX-5
SEL_PH4 = 108     # RX-4
SEL_PH3 = 107     # RX-3
SEL_PH2 = 106     # RX-2
SEL_PH1 = 105     # RX-1
SEL_PH0 = 104     # Phasing RX-0 Position

def preamble(modulator):
    for k in range(0,100*6/2):
        modulator.modulate_symbol([0,1])

def selcall_get_word(value):
    """
    A CCIR 493-4 word consists of a 7-bit word number (0-127), and a 3-bit parity,
    which is the number of 0's in the word.
    The 7-bit word number is send LSB first, then the parity MSB first.
    """
    accum = 0
    lookuptable = [0x0000,0x0200,0x0100,0x0300,0x0080,0x0280,0x0180,0x0380]
    for i in range(0,7):
        if(not((value>>i)&1)):
            accum = accum + 1

    return (value&0x007F)|lookuptable[accum&0x007F]

def selcall_send_word(modulator,symb):
    """
    Modulate a word using the MFSK Modulator.
    """
    if(symb>128):
        return

    current_word = selcall_get_word(symb)
    for i in range(0,10):
        if(current_word&1 == 1):
            modulator.modulate_symbol([1])
        else:
            modulator.modulate_symbol([0])

        current_word = current_word >>1

def selcall_send_message(modulator,message):
    """
    Modulate a selcall message.
    """
    preamble(modulator)

    # CCIR 493-9 specifies error correction, but this is not required for CCIR 493-4.

    # Send Phasing pattern.
    selcall_send_word(modulator,SEL_PDX) # PDX
    selcall_send_word(modulator,SEL_PH5)  # PH5
    selcall_send_word(modulator,SEL_PDX)  # PDX
    selcall_send_word(modulator,SEL_PH4)  # PH4
    selcall_send_word(modulator,SEL_PDX)  # PDX
    selcall_send_word(modulator,SEL_PH3)  # PH3
    selcall_send_word(modulator,SEL_PDX)  # PDX
    selcall_send_word(modulator,SEL_PH2)  # PH2
    selcall_send_word(modulator,SEL_PDX)  # PDX
    selcall_send_word(modulator,SEL_PH1)  # PH1
    selcall_send_word(modulator,SEL_PDX)  # PDX
    selcall_send_word(modulator,SEL_PH0)  # PH0

    for symb in message:
        selcall_send_word(modulator,symb)

def selcall_call(modulator,source,dest):
    """
    Call a 4-digit destination address.
    On most commercial HF radios (Codan, Barrett), this will make the radio ring.
    """
    addr_A1 = (source/100)%100
    addr_A2 = (source%100)
    addr_B1 = (dest/100)%100
    addr_B2 = dest%100

    callmsg = [SEL_SEL, SEL_SEL, addr_B1, SEL_SEL, addr_B2, SEL_SEL, SEL_RTN, addr_B1, addr_A1, addr_B2, addr_A2, SEL_RTN, SEL_ARQ, addr_A1, SEL_ARQ, addr_A2, SEL_ARQ, SEL_ARQ]

    selcall_send_message(modulator,callmsg)

def selcall_chan_test(modulator,source,dest):
    """
    Perform a channel test to a 4-digit selcall address, which causes the recepient
    radio to respond with a 'High-Low-Low-Low-Low' tone sequence.
    This is only confirmed to work with Codan radios.
    """
    addr_A1 = (source/100)%100
    addr_A2 = (source%100)
    addr_B1 = (dest/100)%100
    addr_B2 = dest%100

    callmsg = [SEL_ID, SEL_ID, addr_B1, SEL_ID, addr_B2, SEL_ID, SEL_RTN, addr_B1, addr_A1, addr_B2, addr_A2, SEL_RTN, SEL_ARQ, addr_A1, SEL_ARQ, addr_A2, SEL_ARQ, SEL_ARQ]

    selcall_send_message(modulator,callmsg)

# Test script. Generates a channel test waveform.
if __name__ == "__main__":
    # 1700Hz base tone, 100 baud, 170Hz shift. 30 symbols of silence at the start.
    # NOTE: The tone spacing for this mode is NOT orthogonal. This means the generated waveform will not have
    # constant phase. Sideband can be removed by bandpass filtering the generated signal.
    modulator = mfsk.MFSKModulator(48000,1700,100,170,30,0.5)

    selcall_chan_test(modulator,1882,1881)
    modulator.write_wave('selcall_test_1882_1881.wav')

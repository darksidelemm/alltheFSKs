#!/usr/bin/env python
# MFSKSymbolDecoder.py - Helper class for processing of MFSK symbols.
#
# Probably not required anymore as everything is in ModemUtils.
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

class MFSKSymbolDecoder(object):
    """ MFSK16/32 Symbol Decoder """
    def __init__(self, num_tones = 16, gray_coded = True):
        self.num_tones = num_tones
        self.gray_coded = gray_coded
        self.tone_bits = np.log2(num_tones).astype(np.uint8)

    def gray_decode(self, tone):
        """ Gray-decode the received tone number """
        return (tone>>1)^tone

    def tone_to_bits(self, tone):
        if(tone>= self.num_tones):
            return np.array([]).astype(np.uint8) # Return an empty array.

        if self.gray_coded:
            tone = self.gray_decode(tone)

        return np.unpackbits(np.uint8(tone))[-1*self.tone_bits:]

    def gray_encode(self,data):
        bits = data
        bits ^= data >> 1;
        bits ^= data >> 2;
        bits ^= data >> 3;
        bits ^= data >> 4;
        bits ^= data >> 5;
        bits ^= data >> 6;
        bits ^= data >> 7;

        return bits;

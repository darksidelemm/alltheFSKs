#!/usr/bin/env python
# ModemUtils.py - Some useful functions for modem work.
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

def gray_decode(tone):
    """ Gray-decode the received tone number """
    return (tone>>1)^tone

def gray_encode(data):
    bits = data
    bits ^= data >> 1;
    bits ^= data >> 2;
    bits ^= data >> 3;
    bits ^= data >> 4;
    bits ^= data >> 5;
    bits ^= data >> 6;
    bits ^= data >> 7;

    return bits;

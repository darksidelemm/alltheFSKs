alltheFSKs
==========

Orthogonal Non-Coherent MFSK/FSK Modulator/Demodulator, entirely in Python.

Part of my research work was investigating the various contributions of a modem's transmit/receive chain (i.e. interleaver, FEC rate) to it's robustness in the presence of severe HF disturbances. MFSK modems were investigated as they are quite resilient to doppler and delay spread. I figured that to gain a better understanding of MFSK, writing a modulator & demodulator would be useful.

This modulator is in no way optimized, and at the time of writing runs approximatey 3x slower than realtime. My aim was to write something that could be clearly understood, instead of being a lump of opaque C or fortran code. Hopefully I did a good job on that front. I'm making fairly heavy use of Numpy & Scipy, for example, binary bits are represented as numpy arrays of '0's and '1's.

Classes:
--------
MFSKModulator - Constant Amplitude, Continuous Phase, Orthogonal MFSK Modulator

MFSKDemodulator - Orthogonal MFSK Demodulator

Packetizer - Message packetizer, as per https://docs.google.com/document/d/1fwUtzFUhTzwjHrbfUayRG5sM_3TzdPlPgWjwXnY8fsU/edit

DePacketizer - What it says on the tin. Extracts packets from a bitstream, according to the above doc.

ModemUtils - Helper functions for grey coding and symbol to bitstream conversion.

MFSKSymbolDecoder - Badly named, superfluous helper class, which I'll likely remove shortly.

crc16   - CCITT CRC16 implementation. Should probably be using the internal python one instead.


CCIR493-3 - Implementation of the 'HF SELCALL' standard, as used by Codan and Barrett radios. Transmit only.

Test scripts:
-------------
gen_test_packets.py - Generates a wave file containing MFSK modulated packets.

demod_tests.py - Attempt to demodulate the above using the MFSK Demodulator

demod_SER/BER.py - Run error tests for different Eb/No figures, to validate the modem.


TODO:
-----
- Lots.
- Speed up the demodulator. Making it process more than one sample at a time is probably a good start.
- Add frequency tracking, if this is possible to do for MFSK. 
- Check/fix the Eb/No calculations in the test scripts.
- Add Interleaving & FEC classes. Might see about pulling in LDPC Coding from CML or some other library.

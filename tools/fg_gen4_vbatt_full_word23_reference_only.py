#!/usr/bin/env python3
"""Offline Qualcomm Gen4 VBATT_FULL word23 encoder. NEVER touches device."""
import argparse
WORD, BYTE_OFFSET, NUMERATOR, DENOMINATOR = 23, 0, 1000, 244141
def encode(mv: int):
    if not isinstance(mv, int) or not 0 < mv <= 7000: raise ValueError('invalid mV')
    uv = mv * 1000
    raw = uv * NUMERATOR // DENOMINATOR
    if raw > 0x7fff: raise ValueError('out of range')
    return {'requested_mV':mv, 'sram_word':WORD, 'sram_byte':BYTE_OFFSET,
            'u16':f'0x{raw:04X}', 'little_endian':raw.to_bytes(2,'little').hex(' ').upper(),
            'roundtrip_uV':raw*DENOMINATOR//NUMERATOR, 'is_NOHON_416B_data':False}
if __name__ == '__main__':
    assert encode(4440)['little_endian']=='0A 47'
    assert encode(4490)['little_endian']=='D7 47'
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mv',type=int,nargs='*',default=[4440,4490])
    for v in p.parse_args().mv: print(encode(v))

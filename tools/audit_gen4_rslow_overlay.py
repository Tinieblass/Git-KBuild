#!/usr/bin/env python3
"""Read-only Qualcomm Gen4 DTSI vs simulated Rslow SRAM overlays.

This tool NEVER accesses device SRAM, never writes a kernel profile, and
never produces a flashable battery image. Python 3 standard library only.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def dt_property(source, name, opening, closing):
    cleaned = re.sub(r'/\*.*?\*/|//[^\n]*', '', source, flags=re.S)
    rex = r'\b' + re.escape(name) + r'\s*=\s*' + re.escape(opening)
    rex += r'([^' + re.escape(closing) + r']*)' + re.escape(closing)
    match = re.search(rex, cleaned, flags=re.S)
    if not match:
        raise ValueError('Missing DT property: ' + name)
    return match.group(1).strip()


def profile_bytes(text):
    parts = dt_property(text, 'qcom,fg-profile-data', '[', ']').split()
    if len(parts) != 416 or any(re.fullmatch(r'[0-9a-fA-F]{2}', x) is None
                                for x in parts):
        raise ValueError('Expected exactly 416 hexadecimal bytes')
    return bytearray(int(x, 16) for x in parts)


def rslow(text, which):
    vals = [int(x, 0) for x in dt_property(
        text, 'qcom,rslow-' + which + '-coeffs', '<', '>').split()]
    if len(vals) != 4 or any(not (0 <= x <= 255) for x in vals):
        raise ValueError('Expected four 8-bit Rslow coefficients: ' + which)
    return bytes(vals)


def qcom_checksum(data):
    """Qualcomm UEFI 207-word rotate-left-1 and XOR, NOT CRC16."""
    if len(data) < 414:
        raise ValueError('Profile is shorter than 414 provision bytes')
    checksum = 0
    for i in range(0, 414, 2):
        word = data[i] | (data[i+1] << 8)
        for j in range(4):
            byte = (word >> (8*j)) & 255
            checksum = (((checksum << 1) & 65535) |
                        (checksum >> 15)) ^ byte
    return checksum


def audit(filename):
    raw = Path(filename).read_bytes()
    txt = raw.decode('utf-8')
    data = profile_bytes(txt)
    normal = rslow(txt, 'normal')
    cold = rslow(txt, 'low')
    expected = int(dt_property(txt, 'qcom,checksum', '<', '>'), 0)
    actual = qcom_checksum(data)

    p_normal = data.copy()
    p_normal[26:30] = normal
    p_cold = data.copy()
    p_cold[26:30] = cold
    p_wa = data.copy()
    p_wa[352] &= ~0x02
    p_both = p_cold.copy()
    p_both[352] &= ~0x02

    return {
        'input_file': str(filename),
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'profile_sha256': hashlib.sha256(data).hexdigest(),
        'profile_bytes': len(data),
        'trailing_padding': data[-2:].hex().upper(),
        'internal_nominal_capacity_mAh': int.from_bytes(data[412:414], 'little'),
        'checksum_header': f'{expected:04X}',
        'checksum_recomputed': f'{actual:04X}',
        'checksum_matches': expected == actual,
        'embedded_normal_rslow': data[26:30].hex().upper(),
        'dt_normal_rslow': normal.hex().upper(),
        'dt_cold_rslow': cold.hex().upper(),
        'normal_rslow_matches_embedded': data[26:30] == normal,
        'checksum_normal_overlay': f'{qcom_checksum(p_normal):04X}',
        'checksum_cold_overlay': f'{qcom_checksum(p_cold):04X}',
        'checksum_v1_wa_simulated': f'{qcom_checksum(p_wa):04X}',
        'checksum_cold_plus_v1_wa_simulated': f'{qcom_checksum(p_both):04X}',
        'cold_changed_offsets': [i for i in range(416)
                                 if data[i] != p_cold[i]],
        'cold_first_24_equal': data[:24] == p_cold[:24],
        'cold_first_208_equal': data[:208] == p_cold[:208],
        'workaround_source_byte352': f'{data[352]:02X}',
        'workaround_simulated_byte352': f'{p_wa[352]:02X}',
        'warning': ('Offline simulated SRAM-byte mutation; NOT a real SRAM '
                    'dump, battery characterization, or flashable profile')
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dtsi', nargs='+')
    args = parser.parse_args()
    out = []
    ok = True
    for path in args.dtsi:
        try:
            result = audit(path)
            ok = ok and result['checksum_matches']
            ok = ok and result['normal_rslow_matches_embedded']
            out.append(result)
        except (OSError, ValueError, UnicodeError) as exc:
            out.append({'input_file': path, 'error': str(exc)})
            ok = False
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

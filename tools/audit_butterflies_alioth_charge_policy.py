#!/usr/bin/env python3
"""Read-only offline auditor for alioth battery/charger policy in an AnyKernel ZIP.

Usage: python3 audit_butterflies_alioth_charge_policy.py butterflies-...-5k.zip
Reads a local ZIP, both DTBO images, and their actual alioth FDT overlays.
No boot, DTBO, system or charge parameter is written. No device access.
This checks declared DT configuration, not measured cell terminal voltage.
"""
import argparse
import hashlib
import json
import struct
import sys
import zipfile
from pathlib import Path

FDT_MAGIC = 0xD00DFEED
DTBO_MAGIC = 0xD7B7AB1E
MAX_DECLARED_NOHON_UV = 4_450_000


def u32(data, offset=0):
    return struct.unpack_from('>I', data, offset)[0]


def align4(n):
    return (n + 3) & ~3


def parse_fdt(raw):
    if len(raw) < 40 or u32(raw) != FDT_MAGIC:
        raise ValueError('Not an FDT blob')
    total = u32(raw, 4)
    struct_offset = u32(raw, 8)
    strings_offset = u32(raw, 12)
    strings_size = u32(raw, 32)
    struct_size = u32(raw, 36)
    if any(x > total for x in [struct_offset + struct_size,
                               strings_offset + strings_size]) or total > len(raw):
        raise ValueError('Malformed FDT header bounds')
    strings = raw[strings_offset:strings_offset+strings_size]
    pos, end = struct_offset, struct_offset+struct_size
    stack, out = [], {}
    while pos < end:
        token = u32(raw, pos)
        pos += 4
        if token == 1:
            stop = raw.index(0, pos, end)
            name = raw[pos:stop].decode('utf-8', 'replace')
            stack.append(name)
            pos = align4(stop+1)
        elif token == 2:
            if not stack:
                raise ValueError('Unbalanced FDT node')
            stack.pop()
        elif token == 3:
            length, name_offset = u32(raw, pos), u32(raw, pos+4)
            pos += 8
            if name_offset >= strings_size or pos + length > end:
                raise ValueError('Malformed FDT property')
            stop = strings.index(0, name_offset)
            name = strings[name_offset:stop].decode('utf-8', 'replace')
            path = '/'+'/'.join(x for x in stack if x)
            out.setdefault(path,{})[name] = raw[pos:pos+length]
            pos = align4(pos+length)
        elif token == 4:
            pass
        elif token == 9:
            return out
        else:
            raise ValueError('Unknown FDT structure token: %d' % token)
    raise ValueError('Missing FDT_END token')


def entries(dtbo):
    if len(dtbo) < 32 or u32(dtbo) != DTBO_MAGIC:
        raise ValueError('Not an Android DTBO table')
    length, entry_bytes, count, first = (u32(dtbo,x) for x in (4,12,16,20))
    if length > len(dtbo) or entry_bytes != 32 or first+count*32 > length:
        raise ValueError('Malformed Android DTBO header')
    for i in range(count):
        entry_size, offset, *_ = struct.unpack_from('>8I',dtbo,first+32*i)
        if offset+entry_size > length:
            raise ValueError('Malformed DTBO entry offset')
        image = dtbo[offset:offset+entry_size]
        yield i,image,parse_fdt(image)


def integer_property(props,name):
    raw = props.get(name)
    if raw is None:
        return None
    if len(raw) != 4:
        raise ValueError('Non-u32 property: '+name)
    return u32(raw)


def number_list(props,name):
    raw=props.get(name)
    if raw is None:
        return None
    if len(raw)%4:
        raise ValueError('Non-u32 array: '+name)
    return [u32(raw,p) for p in range(0,len(raw),4)]


def audit_overlay(index,dtbo,file_name):
    matched=[]
    for idx,raw,tree in entries(dtbo):
        root=tree.get('/',{})
        model=root.get('model',b'').split(b'\x00')[0].decode('utf-8','replace')
        board=number_list(root,'qcom,board-id')
        if 'xiaomi alioth' not in model or not board or board[0]!=0x2C:
            continue
        matched.append((idx,raw,tree,model,board))
    if len(matched)!=1:
        raise ValueError('Expected exactly one alioth board 0x2c overlay, found %d' %len(matched))
    idx,raw,tree,model,board=matched[0]
    # Follow the FG controller's actual qcom,battery-data local phandle.
    # Many Xiaomi overlays carry *additional* generic qcom,battery-data nodes
    # elsewhere, and __local_fixups__ mirrors property names with offset arrays.
    # A name scan alone therefore gives a false answer for the active battery.
    fg_refs=[(p,v) for p,v in tree.items()
             if p.endswith('/qpnp,fg') and not p.startswith('/__')
             and 'qcom,battery-data' in v]
    if len(fg_refs)!=1:
        raise ValueError('Ambiguous FG battery-data pointer: %d' % len(fg_refs))
    fg_path,fg_props=fg_refs[0]
    fg_batt_phandle=integer_property(fg_props,'qcom,battery-data')
    battery_nodes=[p for p,v in tree.items()
                   if p.endswith('/qcom,battery-data') and not p.startswith('/__')
                   and integer_property(v,'phandle')==fg_batt_phandle]
    if len(battery_nodes)!=1:
        raise ValueError('Unresolved alioth battery-data phandle: %s' % fg_batt_phandle)
    active_battery_node=battery_nodes[0]

    charge_nodes={}
    prof=[]
    nonselected_profiles=[]
    for path,props in tree.items():
        if path.startswith('/__'):
            continue  # FDT __local_fixups__, __fixups__, __symbols__: NOT runtime nodes
        if path.endswith('/qcom,qpnp-smb5'):
            charge_nodes['smb5']={
                'path':path,
                'fv_max_uv':integer_property(props,'qcom,fv-max-uv'),
                'non_ffc_fv_max_uv':integer_property(props,'qcom,non-fcc-fv-max-uv'),
                'support_ffc_enabled':'mi,support-ffc' in props,
            }
        elif path.endswith('/usbpd_pm'):
            charge_nodes['usbpd_pm']={
                'path':path,
                'pd_bat_volt_max_mv':integer_property(props,'mi,pd-bat-volt-max'),
                'pd_non_ffc_bat_volt_max_mv':integer_property(props,'mi,pd-non-ffc-bat-volt-max'),
            }
        elif path.endswith('/cp_qc30'):
            charge_nodes['qc3']={'path':path,'qc3_bat_volt_max_mv':integer_property(props,'mi,qc3-bat-volt-max')}
        if 'qcom,battery-type' in props:
            name=props['qcom,battery-type'].split(b'\x00')[0].decode('utf-8','replace')
            profile_bytes=props.get('qcom,fg-profile-data',b'')
            jeita=number_list(props,'qcom,jeita-fv-ranges')
            record={'node':path,'battery_type':name,
                    'profile_len':len(profile_bytes),
                    'sha256':hashlib.sha256(profile_bytes).hexdigest(),
                    'max_voltage_uv':integer_property(props,'qcom,max-voltage-uv'),
                    'ffc_cc_cv_mv':integer_property(props,'qcom,fg-ffc-cc-cv-threshold-mv'),
                    'jeita_float_uv':jeita[2::3] if jeita else None}
            if path.startswith(active_battery_node+'/'):
                prof.append(record)
            else:
                nonselected_profiles.append(record)
    probes=[]
    def consider(name,value_uv):
        if value_uv is not None:
            probes.append({'field':name,'configured_uv':value_uv,
                           'above_4450_mV':value_uv>MAX_DECLARED_NOHON_UV,
                           'delta_uv':value_uv-MAX_DECLARED_NOHON_UV})
    smb=charge_nodes.get('smb5',{})
    pd=charge_nodes.get('usbpd_pm',{})
    qc=charge_nodes.get('qc3',{})
    consider('smb5.fv_max_uv',smb.get('fv_max_uv'))
    consider('smb5.non_ffc_fv_max_uv',smb.get('non_ffc_fv_max_uv'))
    consider('usbpd_pm.pd_bat_volt_max_mv',pd.get('pd_bat_volt_max_mv')*1000 if pd.get('pd_bat_volt_max_mv') is not None else None)
    consider('usbpd_pm.pd_non_ffc_bat_volt_max_mv',pd.get('pd_non_ffc_bat_volt_max_mv')*1000 if pd.get('pd_non_ffc_bat_volt_max_mv') is not None else None)
    consider('qc3.qc3_bat_volt_max_mv',qc.get('qc3_bat_volt_max_mv')*1000 if qc.get('qc3_bat_volt_max_mv') is not None else None)
    for p in prof:
        consider('profile.'+p['battery_type']+'.max_voltage_uv',p['max_voltage_uv'])
        consider('profile.'+p['battery_type']+'.ffc_cc_cv_mv',p['ffc_cc_cv_mv']*1000 if p['ffc_cc_cv_mv'] is not None else None)
        if p['jeita_float_uv']:
            consider('profile.'+p['battery_type']+'.max_jeita_fv_uv',max(p['jeita_float_uv']))
    return {'dtbo_file':file_name,'dtbo_sha256':hashlib.sha256(dtbo).hexdigest(),
            'alioth_entry_index':idx,'alioth_model':model,'board_id':board[0],
            'alioth_overlay_sha256':hashlib.sha256(raw).hexdigest(),
            'chargers':charge_nodes,
            'fg_battery_data_ref_path':fg_path,
            'fg_battery_data_phandle':fg_batt_phandle,
            'selected_battery_data_path':active_battery_node,
            'fg_profile_nodes':prof,
            'other_embedded_battery_profiles_not_selected_by_this_fg':nonselected_profiles,
            'charged_voltage_configuration':probes,
            'fields_above_declared_nohon_limit':[p for p in probes if p['above_4450_mV']],
            'warning':'Configured limit/thresholds, NOT measured terminal voltage or evidence of active charging path'}


def audit(zip_path):
    zip_path=Path(zip_path)
    with zipfile.ZipFile(zip_path) as z:
        names=set(z.namelist())
        if 'dtbo.img' not in names or '5k/dtbo.img' not in names:
            raise ValueError('Expected default and 5k DTBO payloads')
        lower=zip_path.name.lower()
        selected='5k/dtbo.img' if '5k' in lower else 'dtbo.img'
        scans=[audit_overlay(i,z.read(i),i) for i in ('dtbo.img','5k/dtbo.img')]
    return {'kind':'OFFLINE_DTBO_CONFIG_AUDIT__NOT_PHYSICAL_CELL_VOLTAGE',
            'file':str(zip_path), 'zip_sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest(),
            'selection_based_on_zip_basename':selected,
            'declared_nohon_cell_voltage_limit_uv':MAX_DECLARED_NOHON_UV,
            'results':scans,
            'battery_model_reconstructed':False,'safe_to_flash':False,
            'note':'Binary analysis only; runtime chip mode and actual phone partitions/charging voltages unverified'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip_path')
    args=parser.parse_args()
    try:
        print(json.dumps(audit(args.zip_path),indent=2,ensure_ascii=False))
    except (ValueError,OSError,zipfile.BadZipFile,struct.error) as e:
        print(json.dumps({'error':str(e),'safe_to_flash':False}),file=sys.stderr)
        sys.exit(1)
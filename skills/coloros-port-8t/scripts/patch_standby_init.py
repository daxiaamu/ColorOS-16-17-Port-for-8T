"""Prepare target-specific init candidates; never flashes a device."""
import argparse, hashlib, pathlib, re

def patch(text, kind):
    if kind == 'laser':
        pattern = r'(?m)^service vl53l1_daemon_main /odm/bin/vl53l1_daemon_main\n(?:[ \t]+[^\n]*\n)+'
        matches = list(re.finditer(pattern, text))
        if len(matches) != 1 or 'socket vl53l1_daemon' not in matches[0].group():
            raise ValueError('Expected exactly one original laser service block')
        return re.sub(pattern, '# Target has no stmvl53l1 hardware interface; omit unsupported service.\n', text)
    if text.count('service loc_sys_service ') != 1 or text.count('start loc_sys_service') != 1:
        raise ValueError('Expected original donor location helper definition and start')
    return ('# This target uses vendor HIDL GNSS and native XTRA.\n'
            '# Omit the incompatible donor AIDL-only configuration helper.\n')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind', choices=['laser', 'location'])
    p.add_argument('source', type=pathlib.Path)
    p.add_argument('output', type=pathlib.Path)
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--confirmed-target-compatibility', action='store_true', required=True,
                   help='Caller verified absent laser interface or HIDL-only vendor as applicable')
    a = p.parse_args()
    data = a.source.read_bytes()
    if hashlib.sha256(data).hexdigest() != a.expected_sha256.lower():
        raise ValueError('Input SHA256 mismatch')
    result = patch(data.decode('utf-8').replace('\r\n', '\n'), a.kind)
    with a.output.open('xb') as f:
        f.write(result.encode('utf-8'))
    print(hashlib.sha256(result.encode('utf-8')).hexdigest())

if __name__ == '__main__':
    main()

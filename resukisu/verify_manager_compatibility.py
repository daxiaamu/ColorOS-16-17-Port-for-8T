#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
r=Path(__file__).resolve().parent; k=Path(sys.argv[1]); expected=json.loads((r/'manager-compatibility.json').read_text())
s=(k/'manager/manager_sign.h').read_text()
h=re.search(r'#define EXPECTED_HASH_RESUKISU "([a-f0-9]+)"',s).group(1)
n=int(re.search(r'#define EXPECTED_SIZE_RESUKISU (\S+)',s).group(1),0)
assert h==expected['official_certificate_sha256'] and n==expected['official_certificate_size']
s=(k/'manager/apk_sign.c').read_text()
assert '{ EXPECTED_SIZE_RESUKISU, EXPECTED_HASH_RESUKISU }' in s
assert '{ EXPECTED_SIZE, EXPECTED_HASH }' in s
build=(r/'build_kernel.sh').read_text()
assert 'KSU_MANAGER_PACKAGE=' not in build
assert 'KSU_EXPECTED_HASH=' not in build
print('Official TG/Actions certificate retained; no custom certificate override')

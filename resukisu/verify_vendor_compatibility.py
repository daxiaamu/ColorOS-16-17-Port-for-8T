#!/usr/bin/env python3
"""Reject kernels that cannot load the unchanged kebab vendor modules."""
from pathlib import Path
import argparse,hashlib,json,ssl
p=argparse.ArgumentParser();p.add_argument('image',type=Path);p.add_argument('symvers',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
r=Path(__file__).resolve().parent
baseline=json.loads((r/'kebab-vendor-abi.json').read_text())
cert=ssl.PEM_cert_to_DER_cert((r/'kebab-stock-module-cert.pem').read_text())
assert hashlib.sha256(cert).hexdigest()==baseline['certificate_sha256']
actual={line.split()[1]:int(line.split()[0],16) for line in a.symvers.read_text().splitlines() if len(line.split())>=2}
mismatches={name:{'expected':crc,'actual':hex(actual[name]) if name in actual else None} for name,crc in baseline['kernel_imports'].items() if actual.get(name)!=int(crc,16)}
report={'oem_module_certificate_present':cert in a.image.read_bytes(),'checked_kernel_imports':len(baseline['kernel_imports']),'abi_mismatches':mismatches,'scope':'Imported kernel symbols and OEM trust certificate; device boot and module load tests still required.'}
a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
print(f"OEM certificate present: {report['oem_module_certificate_present']}; ABI mismatches: {len(mismatches)}")
if mismatches or not report['oem_module_certificate_present']:
 raise SystemExit('Kernel is incompatible with stock vendor modules; do not package or flash it. See '+str(a.report))

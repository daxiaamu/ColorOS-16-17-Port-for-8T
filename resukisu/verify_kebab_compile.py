#!/usr/bin/env python3
"""Require guarded fixes to be enabled in actual driver compilation commands."""
import argparse,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('--report',type=Path);a=p.parse_args()
checks=[('techpack/display/msm/dsi/.dsi_panel.o.cmd','OPLUS_BUG_STABILITY'),('drivers/misc/aw8697_haptic/.aw8697.o.cmd','CONFIG_OPLUS_HAPTIC_OOS')]
results=[]
for relative,macro in checks:
 path=a.out/relative
 assert path.is_file(), 'Driver was not compiled: '+str(path)
 command=path.read_text().splitlines()[0]
 assert re.search(r'(?:^|\s)-D'+macro+r'(?:=1)?(?:\s|$)',command), 'Required macro missing from compiler command: '+macro
 results.append({'object_command':relative,'enabled_macro':macro})
print(json.dumps(results,indent=2))
if a.report: a.report.write_text(json.dumps(results,indent=2)+'\n')

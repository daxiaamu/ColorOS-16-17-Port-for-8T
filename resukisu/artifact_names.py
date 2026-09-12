#!/usr/bin/env python3
"""Shared release filenames; Actions supplies one Beijing date to every job."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json, os, re

def artifact_names(build_date=None):
 sources=json.loads(Path(__file__).with_name('sources.json').read_text())
 match=re.fullmatch(r'ReSukiSU_(v[0-9][A-Za-z0-9.-]*)_([0-9]+)-arm64-v8a-release\.apk',sources['official_manager_apk'])
 if not match: raise ValueError('Unrecognized locked official APK filename')
 version,code=match.groups()
 date=build_date or os.environ.get('RESUKISU_BUILD_DATE') or datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d')
 if not re.fullmatch(r'[0-9]{8}',date): raise ValueError('Build date must be YYYYMMDD')
 datetime.strptime(date,'%Y%m%d')
 prefix=f'ReSukiSU_{version}_{code}_{date}'
 return {'prefix':prefix,'version':version,'version_code':code,'build_date':date,
         'boot':prefix+'_kebab_boot.img','twrp':prefix+'_kebab_TWRP.zip',
         'apk':prefix+'_arm64-v8a-release.apk'}

if __name__=='__main__':
 names=artifact_names()
 if os.environ.get('GITHUB_OUTPUT'):
  with open(os.environ['GITHUB_OUTPUT'],'a') as output:
   for key in ('prefix','build_date'): output.write(f'{key}={names[key]}\n')
 print(json.dumps(names,indent=2))

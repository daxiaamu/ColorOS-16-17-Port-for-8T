#!/usr/bin/env python3
# Negative tests: device and slot guards must abort before any partition access/write.
import os,subprocess,tempfile
from pathlib import Path
script=Path(__file__).with_name('update-binary').resolve()
with tempfile.TemporaryDirectory() as d:
 root=Path(d); marker=root/'write-attempt'
 (root/'getprop').write_text('#!/bin/sh\ncase "$1" in ro.boot.project_name) echo "$TEST_PROJECT";; ro.boot.slot_suffix) echo "$TEST_SLOT";; esac\n')
 (root/'cat').write_text('#!/bin/sh\n[ "$1" != /proc/oplusVersion/prjName ] || exit 1\nexec /bin/cat "$@"\n')
 (root/'dd').write_text('#!/bin/sh\ntouch "'+str(marker)+'"\nexit 99\n')
 for p in root.iterdir(): p.chmod(0o755)
 for project,slot,expected in [('99999','_a','Wrong boot project'),('','','Missing 8T hardware identity'),('19805','','Unknown slot'),('19805','_c','Unknown slot')]:
  env=dict(os.environ,PATH=d+':'+os.environ['PATH'],TEST_PROJECT=project,TEST_SLOT=slot)
  p=subprocess.run(['sh',str(script),'3','1','unused.zip'],env=env,capture_output=True,text=True)
  assert p.returncode!=0 and expected in p.stdout,(project,slot,p.stdout,p.stderr)
  assert not marker.exists(),'Installer attempted to write before validation'
print('Installer device/slot rejection tests passed')

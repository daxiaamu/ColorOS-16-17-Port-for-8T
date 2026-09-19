#!/usr/bin/env python3
"""Run installer against regular files only; never access real partitions."""
import hashlib,json,os,subprocess,tempfile,zipfile
from pathlib import Path
from boot_compatibility import compatible_hashes
R=Path(__file__).resolve().parent
size=4096
old=b'A'*size; rom=b'B'*size; target=b'C'*size; unknown=b'D'*size
sha=lambda b:hashlib.sha256(b).hexdigest()
script=(R/'update-binary').read_text().replace('@FROM_HASH@',sha(old)).replace('@COMPATIBLE_HASHES@',sha(rom)).replace('@TO_HASH@',sha(target))
count=0
for label,initial,payload,fault,backup in [
 ('old',old,target,False,None),('rom',rom,target,False,None),
 ('already',target,target,False,None),('unknown',unknown,target,False,None),
 ('bad-payload',rom,unknown,False,None),('short-payload',rom,b'x',False,None),
 ('valid-existing-backup',rom,target,False,rom),('bad-existing-backup',rom,target,False,unknown),
 ('rollback-old',old,target,True,None),('rollback-rom',rom,target,True,None)]:
 with tempfile.TemporaryDirectory(prefix='boot-installer-') as d:
  root=Path(d);part=root/'boot_a';part.write_bytes(initial);backups=root/'backup';backups.mkdir();binpath=root/'bin';binpath.mkdir()
  if backup is not None:(backups/('boot_a_'+sha(initial)+'.img')).write_bytes(backup)
  # Instrument only filesystem endpoints, block-device type and fixture size.
  test=script.replace('PART="/dev/block/by-name/boot$SLOT"','PART="'+str(root)+'/boot$SLOT"').replace('[ -b "$PART" ]','[ -f "$PART" ]').replace('BACKUPDIR=/sdcard/ReSukiSU-8T-backup','BACKUPDIR='+str(backups)).replace('100663296',str(size))
  (root/'installer').write_text(test)
  stubs={
   'getprop':'case "$1" in ro.boot.project_name) echo 19805;; ro.boot.slot_suffix) echo _a;; esac',
   'cat':'[ "$1" != /proc/oplusVersion/prjName ] || exit 1\nexec /bin/cat "$@"',
   'blockdev':'echo '+str(size),
   'dd':'''for arg in "$@"; do case "$arg" in if=*) src=${arg#if=};; of=*) dst=${arg#of=};; esac; done
if [ "$dst" = "$TEST_PART" ]; then
 echo write >> "$TEST_WRITES"
 if [ "$TEST_FAULT" = 1 ] && [ ! -f "$TEST_FAILED" ]; then
  touch "$TEST_FAILED"; printf broken > "$dst"; exit 1
 fi
fi
exec /bin/dd "$@"'''}
  for name,body in stubs.items():
   p=binpath/name;p.write_text('#!/bin/sh\n'+body+'\n');p.chmod(0o755)
  archive=root/'payload.zip'
  with zipfile.ZipFile(archive,'w') as z:z.writestr('images/boot.img',payload)
  env=dict(os.environ,PATH=str(binpath)+':'+os.environ['PATH'],TEST_PART=str(part),TEST_WRITES=str(root/'writes'),TEST_FAILED=str(root/'failed'),TEST_FAULT=str(int(fault)))
  result=subprocess.run(['sh',str(root/'installer'),'3','1',str(archive)],env=env,capture_output=True,text=True)
  writes=(root/'writes').read_text().splitlines() if (root/'writes').exists() else []
  success=label in ('old','rom','already','valid-existing-backup')
  assert (result.returncode==0)==success,(label,result.stdout,result.stderr)
  if success:
   assert part.read_bytes()==target
   assert len(writes)==(0 if label=='already' else 1)
   if label!='already':assert (backups/('boot_a_'+sha(initial)+'.img')).read_bytes()==initial
  else:
   assert part.read_bytes()==initial,label
   assert len(writes)==(2 if fault else 0),label
   if fault:assert 'Original boot restored' in result.stdout
  count+=1
# Reject incompatible metadata before a package can widen its accepted hashes.
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'compat.json';parts={'header':'1','dtb':'2','ramdisk.cpio':'3'}
 row={'sha256':sha(rom),'bytes':size,'preserved_components':parts}
 p.write_text(json.dumps({'schema':1,'boots':[row]}));assert compatible_hashes(p,parts,size)==[sha(rom)]
 for field,value in [('sha256','*'),('bytes',1),('preserved_components',{'dtb':'different'})]:
  p.write_text(json.dumps({'schema':1,'boots':[dict(row,**{field:value})]}))
  try:compatible_hashes(p,parts,size)
  except AssertionError:pass
  else:raise AssertionError('Accepted invalid compatibility metadata: '+field)
print('PASS: %d installer cases including both-base rollback; component/size/hash guards passed'%count)

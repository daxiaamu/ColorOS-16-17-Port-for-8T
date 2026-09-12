#!/usr/bin/env python3
"""Exercise the actual installer logic against tiny regular files, never devices."""
import hashlib,os,subprocess,tempfile,zipfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'resukisu/update-binary').read_text(encoding='utf-8')
old=b'A'*1024; new=b'B'*1024
sha=lambda b:hashlib.sha256(b).hexdigest()

@unittest.skipUnless(os.name == "posix", "requires POSIX shell")
class InstallerFileTests(unittest.TestCase):
    def test_install_and_recovery_paths(self):
        for mode in ['success','wrong_base','corrupt_payload','write_failure','already_installed','wrong_size']:
         with tempfile.TemporaryDirectory(prefix='resukisu-installer-test-') as tmp:
          root=Path(tmp); partition=root/'boot_a'; backup=root/'backup'; bindir=root/'bin'; bindir.mkdir()
          initial=(new if mode=='already_installed' else (b'C'*1024 if mode=='wrong_base' else old))
          if mode=='wrong_size': initial+=b'X'
          partition.write_bytes(initial)
          script=source.replace('PART="/dev/block/by-name/boot$SLOT"','PART="'+str(partition)+'"').replace('[ -b "$PART" ]','[ -f "$PART" ]').replace('BACKUPDIR=/sdcard/ReSukiSU-8T-backup','BACKUPDIR='+str(backup)).replace('100663296','1024').replace('@FROM_HASH@',sha(old)).replace('@TO_HASH@',sha(new))
          (root/'installer').write_text(script)
          (bindir/'getprop').write_text('#!/bin/sh\ncase "$1" in ro.boot.project_name) echo 19805;; ro.boot.slot_suffix) echo _a;; esac\n')
          (bindir/'cat').write_text('#!/bin/sh\n[ "$1" != /proc/oplusVersion/prjName ] || exit 1\nexec /bin/cat "$@"\n')
          (bindir/'blockdev').write_text('#!/bin/sh\nstat -c %s "$2"\n')
          (bindir/'dd').write_text('''#!/bin/sh
        for arg in "$@"; do
         case "$arg" in if=*) input=${arg#if=};; of=*) output=${arg#of=};; esac
        done
        case "$output" in "$TEST_ROOT"/*) ;; *) echo 'TEST SAFETY: write outside fixture' >&2; exit 80;; esac
        if [ "$TEST_MODE" = write_failure ]; then
         case "$input" in */new.img) printf BROKEN > "$output"; exit 1;; esac
        fi
        exec /bin/dd "$@"
        ''')
          for p in bindir.iterdir():p.chmod(0o755)
          with zipfile.ZipFile(root/'patch.zip','w') as z:z.writestr('images/boot.img',b'C'*1024 if mode=='corrupt_payload' else new)
          env=dict(os.environ,PATH=str(bindir)+':'+os.environ['PATH'],TEST_ROOT=tmp,TEST_MODE=mode)
          result=subprocess.run(['sh',str(root/'installer'),'3','1',str(root/'patch.zip')],env=env,capture_output=True,text=True)
          if mode in ['success','already_installed']:
           assert result.returncode==0,(mode,result.stdout,result.stderr)
           assert partition.read_bytes()==new
          else:
           assert result.returncode!=0,(mode,result.stdout,result.stderr)
           assert partition.read_bytes()==initial,(mode,'partition changed after rejection/failure')
          if mode in ['success','write_failure']:
           assert (backup/('boot_a_'+sha(old)+'.img')).read_bytes()==old
          if mode=='write_failure':assert 'Original boot restored' in result.stdout
          print(mode+': PASS')

if __name__ == "__main__":
    unittest.main()

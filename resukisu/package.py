#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,gzip,json,os,shutil,subprocess,urllib.request,zipfile
from boot_compatibility import compatible_hashes
from artifact_names import artifact_names
parser=argparse.ArgumentParser()
parser.add_argument('--rom',required=True,choices=['ColorOS16','ColorOS17'])
args=parser.parse_args()
N=artifact_names(rom=args.rom)
R=Path(__file__).resolve().parent; S=json.loads((R/'sources.json').read_text()); W=(Path('packaging-work')/args.rom).resolve(); W.mkdir(parents=True); D=(Path('dist')/args.rom).resolve(); D.mkdir(parents=True)
assert json.loads(Path('kernel-output/sources.json').read_text()) == S, 'Kernel/package source locks differ'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fetch(url,path,digest):
 subprocess.run(['curl','-fL','--retry','3','--connect-timeout','30',url,'-o',str(path)],check=True)
 assert sha(path)==digest, f'Download hash mismatch: {url}'
fetch(S['base_boot_url'],W/'base.gz',S['base_boot_gz_sha256'])
base=W/'base.img'; base.write_bytes(gzip.decompress((W/'base.gz').read_bytes())); assert sha(base)==S['base_boot_sha256']
fetch('https://github.com/topjohnwu/Magisk/releases/download/v30.7/Magisk-v30.7.apk',W/'Magisk.apk','e0d32d2123532860f97123d927b1bb86c4e08e6fd8a48bfc6b5bee0afae9ebd5')
mb=W/'magiskboot'
with zipfile.ZipFile(W/'Magisk.apk') as z: mb.write_bytes(z.read('lib/x86_64/libmagiskboot.so'))
mb.chmod(0o755)
def run(*args,cwd): subprocess.run([str(mb),*map(str,args)],cwd=cwd,check=True)
work=W/'repack'; work.mkdir(); run('unpack','-h',base,cwd=work)
original={p.name:sha(p) for p in work.iterdir() if p.is_file() and p.name!='kernel'}
assert 'ramdisk.cpio' in original and 'dtb' in original
profile_path=R/'profiles'/(args.rom+'.json')
profile=json.loads(profile_path.read_text())
assert profile['rom']==args.rom
accepted_hashes=compatible_hashes(profile_path,original,S['boot_partition_bytes'])
assert accepted_hashes, 'ROM must have an explicit accepted boot list'
# Reject rooted/private boot inputs, even if a future lockfile accidentally points to one.
run('cpio','ramdisk.cpio','test',cwd=work)
ramdisk=(work/'ramdisk.cpio').read_bytes()
for marker in [b'adb_keys',b'init.magisk.rc',b'.backup/.magisk',b'overlay.d/sbin']:
 assert marker not in ramdisk, f'Unexpected root/private boot content: {marker}'
shutil.copyfile('kernel-output/Image',work/'kernel')
run('repack',base,D/N['boot'],cwd=work)
p=D/N['boot']; assert p.stat().st_size<=S['boot_partition_bytes']
with p.open('ab') as f: f.write(b'\0'*(S['boot_partition_bytes']-p.stat().st_size))
verify=W/'verify'; verify.mkdir(); run('unpack','-h',p,cwd=verify)
assert sha(verify/'kernel')==sha(Path('kernel-output/Image'))
for name,digest in original.items(): assert sha(verify/name)==digest, f'Boot component changed: {name}'
newsha=sha(p)
manifest={'artifact_names':N,'rom':args.rom,'rom_baseline':profile['baseline'],'rom_profile':profile,'status':'compiled-and-offline-verified; NOT device-boot-tested','device':'OnePlus 8T KB2000 / project 19805','slot_policy':'current only; no slot switch','base_boot_sha256':S['base_boot_sha256'],'accepted_boot_sha256':accepted_hashes,'boot_sha256':newsha,'boot_bytes':p.stat().st_size,'preserved_components':original,'source_locks':S,'module_abi_runtime_validation':'pending','selinux':'original enforcing configuration retained','manager_support':'official ReSukiSU Actions/TG certificate; see manager-compatibility.json'}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# The standalone download and ZIP payload share this single repacked image.
script=(R/'update-binary').read_text().replace('@FROM_HASH@',accepted_hashes[0]).replace('@TO_HASH@',newsha).replace('@COMPATIBLE_HASHES@',' '.join(accepted_hashes[1:])).replace('@ROM_NAME@',args.rom)
with zipfile.ZipFile(D/N['twrp'],'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 entry=zipfile.ZipInfo('META-INF/com/google/android/update-binary'); entry.external_attr=0o100755<<16; z.writestr(entry,script)
 z.writestr('META-INF/com/google/android/updater-script','# Handled by update-binary\n')
 z.write(p,'images/boot.img'); z.write(D/'manifest.json','manifest.json')
with zipfile.ZipFile(D/N['twrp']) as z:
 assert z.testzip() is None
 digest=hashlib.sha256()
 with z.open('images/boot.img') as payload:
  for block in iter(lambda:payload.read(1024*1024),b''): digest.update(block)
 assert digest.hexdigest()==newsha, 'Standalone boot differs from TWRP payload'
shutil.copyfile(R/'README.md',D/'README.md')
shutil.copyfile(R/'manager-compatibility.json',D/'manager-compatibility.json')
(D/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(D.iterdir()) if p.is_file()))
print(json.dumps(manifest,indent=2))

#!/usr/bin/env python3
from pathlib import Path
import subprocess, json, shutil, os
R=Path(__file__).resolve().parent
S=json.loads((R/'sources.json').read_text())
W=Path('build').resolve(); W.mkdir(exist_ok=True)
def run(*cmd,**kw): subprocess.run(cmd,check=True,**kw)
def clone(url,sha,path,full=False):
 if path.exists(): raise SystemExit(f'Refusing existing source directory: {path}')
 if full:
  run('git','clone',url,str(path))
 else:
  path.mkdir(parents=True); run('git','init',str(path)); run('git','-C',str(path),'remote','add','origin',url)
  run('git','-C',str(path),'fetch','--depth=1','origin',sha)
 run('git','-C',str(path),'checkout','--detach',sha)
 assert subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()==sha
K=W/'src/kernel/msm'
clone(S['kernel_repo'],S['kernel_commit'],K)
clone(S['modules_repo'],S['modules_commit'],W/'modules')
(W/'src/vendor').symlink_to('../modules/vendor',target_is_directory=True)
(K.parent/'msm-4.19').symlink_to('msm',target_is_directory=True)
shutil.copytree(W/'modules/kernel/msm-4.19/techpack',K/'techpack',dirs_exist_ok=True,symlinks=True)
shutil.copytree(W/'modules/vendor/qcom/opensource/audio-kernel',K/'techpack/audio',symlinks=True)
clone(S['resukisu_repo'],S['resukisu_commit'],K/'KernelSU',full=True)
# Some official source files have CRLF; normalize text without touching blobs/symlinks.
for base in [K,W/'modules']:
 for directory,dirs,files in os.walk(base):
  dirs[:]=[d for d in dirs if d!='.git']
  for name in files:
   p=Path(directory)/name
   if p.is_symlink(): continue
   b=p.read_bytes()
   if b'\0' not in b and b'\r\n' in b: p.write_bytes(b.replace(b'\r\n',b'\n'))
# GNU empty aggregate initialization is equivalent to zero initialization, and
# avoids Clang 10's nested-aggregate missing-braces diagnostic in vendor code.
fixes=[
 (K/'drivers/soc/oplus/storage/common/io_metrics/block_metrics.c','= {0};','= {};',3),
 (K/'drivers/soc/oplus/storage/common/io_metrics/f2fs_metrics.c','= {0};','= {};',2),
 (K/'drivers/soc/oplus/storage/common/io_metrics/ufs_metrics.c','= {0};','= {};',2),
 (K/'drivers/power/oplus/v1/voocphy/oplus_voocphy.c','= {0};','= {};',13),
 (K/'drivers/power/oplus/v1/wireless_ic/oplus_nu1619.c','[TABLE_MAX] = {0};','[TABLE_MAX] = {};',5),
 (K/'drivers/power/oplus/v1/vooc_ic/oplus_vooc_fw.c','= {0};','= {};',6),
 (K/'net/oplus_modules/data_module/dpi/dpi_core.c','dpi_tuple_t tuple = {0};','dpi_tuple_t tuple = {};',2),
 (K/'drivers/power/oplus/v1/ufcs/oplus_ufcs_protocol.c','struct verify_request req = { 0 };','struct verify_request req = {};',1),
 (K/'drivers/power/oplus/v1/ufcs/oplus_ufcs_protocol.c','struct verify_response resp = { 0 };','struct verify_response resp = {};',1),
]
for path,before,after,count in fixes:
 text=path.read_text(); assert text.count(before)==count,(path,before)
 path.write_text(text.replace(before,after))
run('python3',str(R/'prepare_hooks.py'),str(K),'--patch-out',str(W/'manual-hooks.patch'))
p=K/'scripts/gcc-wrapper.py'; t=p.read_text()
t=t.replace('print "error, forbidden warning:", m.group(2)','print("error, forbidden warning:", m.group(2))').replace('print line,','print(line, end="")').replace("print args[0] + ':',e.strerror","print(args[0] + ':',e.strerror)").replace("print 'Is your PATH set correctly?'","print('Is your PATH set correctly?')").replace("print ' '.join(args), str(e)","print(' '.join(args), str(e))").replace('stderr=subprocess.PIPE)','stderr=subprocess.PIPE, universal_newlines=True)')
p.write_text(t)
(W/'out').mkdir(); shutil.copyfile(R/'stock.config',W/'out/.config')
run(str(K/'scripts/config'),'--file',str(W/'out/.config'),'-e','KSU','-e','KSU_MANUAL_HOOK','-d','KSU_TRACEPOINT_HOOK','-e','KSU_MANUAL_HOOK_AUTO_SETUID_HOOK','-e','KSU_MANUAL_HOOK_AUTO_INITRC_HOOK','-e','KSU_MANUAL_HOOK_AUTO_INPUT_HOOK','-e','KSU_MULTI_MANAGER_SUPPORT','-d','KSU_SUSFS','-d','KSU_DEBUG')
(W/'bin').mkdir(); (W/'bin/python').symlink_to(shutil.which('python3'))

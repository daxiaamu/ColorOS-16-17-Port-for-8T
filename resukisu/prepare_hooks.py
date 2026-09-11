# SPDX-License-Identifier: GPL-3.0-only
# Adapted from https://resukisu.org/guide/manual-integrate.html
"""Apply pinned ReSukiSU manual hooks to the official OnePlus 8T kernel."""
from pathlib import Path
import argparse, difflib
p=argparse.ArgumentParser(); p.add_argument('kernel',type=Path); p.add_argument('--patch-out',type=Path,required=True); a=p.parse_args()
r=a.kernel.resolve(); diffs=[]
def hook(s): return '#ifdef CONFIG_KSU_MANUAL_HOOK\n'+s+'\n#endif\n'
def edit(name, ops):
 path=r/name; old=path.read_text(); new=old
 for before,after,count in ops:
  assert new.count(before)==count,(name,before,new.count(before))
  new=new.replace(before,after)
 path.write_text(new)
 diffs.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),'a/'+name,'b/'+name))
edit('fs/exec.c',[
 ('static int do_execveat_common(',hook('extern int ksu_handle_execveat(int *fd, struct filename **filename_ptr, void *argv, void *envp, int *flags);')+'\nstatic int do_execveat_common(',1),
 ('\treturn __do_execve_file(fd, filename, argv, envp, flags, NULL);',hook('\tksu_handle_execveat(&fd, &filename, &argv, &envp, &flags);')+'\treturn __do_execve_file(fd, filename, argv, envp, flags, NULL);',1)])
edit('fs/open.c',[
 ('SYSCALL_DEFINE3(faccessat,',hook('extern int ksu_handle_faccessat(int *dfd, const char __user **filename_user, int *mode, int *flags);')+'\nSYSCALL_DEFINE3(faccessat,',1),
 ('\treturn do_faccessat(dfd, filename, mode);',hook('\tksu_handle_faccessat(&dfd, &filename, &mode, NULL);')+'\treturn do_faccessat(dfd, filename, mode);',1)])
decl=hook('extern int ksu_handle_stat(int *dfd, const char __user **filename_user, int *flags);\nextern void ksu_handle_newfstat_ret(unsigned int *fd, struct stat __user **statbuf_ptr);\n#if defined(__ARCH_WANT_STAT64) || defined(__ARCH_WANT_COMPAT_STAT64)\nextern void ksu_handle_fstat64_ret(unsigned long *fd, struct stat64 __user **statbuf_ptr);\n#endif')
oldf='SYSCALL_DEFINE2(fstat64, unsigned long, fd, struct stat64 __user *, statbuf)\n{\n\tstruct kstat stat;\n\tint error = vfs_fstat(fd, &stat);\n\n\tif (!error)\n\t\terror = cp_new_stat64(&stat, statbuf);\n\n'
edit('fs/stat.c',[
 ('#if !defined(__ARCH_WANT_STAT64) || defined(__ARCH_WANT_SYS_NEWFSTATAT)',decl+'\n#if !defined(__ARCH_WANT_STAT64) || defined(__ARCH_WANT_SYS_NEWFSTATAT)',1),
 ('\terror = vfs_fstatat(dfd, filename, &stat, flag);',hook('\tksu_handle_stat(&dfd, &filename, &flag);')+'\terror = vfs_fstatat(dfd, filename, &stat, flag);',3),
 ('\t\terror = cp_new_stat(&stat, statbuf);\n\n\treturn error;','\t\terror = cp_new_stat(&stat, statbuf);\n\n'+hook('\tksu_handle_newfstat_ret(&fd, &statbuf);')+'\treturn error;',1),
 (oldf+'\treturn error;',oldf+hook('\tksu_handle_fstat64_ret(&fd, &statbuf);')+'\treturn error;',1)])
edit('kernel/reboot.c',[
 ('SYSCALL_DEFINE4(reboot,',hook('extern int ksu_handle_sys_reboot(int magic1, int magic2, unsigned int cmd, void __user **arg);')+'\nSYSCALL_DEFINE4(reboot,',1),
 ('\t/* We only trust the superuser with rebooting the system. */',hook('\tksu_handle_sys_reboot(magic1, magic2, cmd, &arg);')+'\t/* We only trust the superuser with rebooting the system. */',1)])
edit('drivers/Makefile',[('# SPDX-License-Identifier: GPL-2.0','# SPDX-License-Identifier: GPL-2.0\nobj-$(CONFIG_KSU) += kernelsu/',1)])
edit('drivers/Kconfig',[('menu "Device Drivers"','menu "Device Drivers"\nsource "drivers/kernelsu/Kconfig"',1)])
(r/'drivers/kernelsu').symlink_to('../KernelSU/kernel',target_is_directory=True)
a.patch_out.write_text(''.join(diffs)); print('Manual hooks applied:',a.patch_out)


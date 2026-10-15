#!/usr/bin/env python3
"""Run the actual policy initializer with/without OF2FS; reject collateral changes."""
import argparse,json,os,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('kernel');p.add_argument('--report');a=p.parse_args()
s=(Path(a.kernel)/'fs/f2fs/segment.c').read_text()
start=s.index('static void __init_discard_policy(');end=s.index('\nstatic void __update_discard_tree_range',start);fn=s[start:end]
needle='dpolicy->granularity = 1;\n\t\tdpolicy->timeout = true;\n#ifdef CONFIG_OPLUS_FEATURE_OF2FS'
assert fn.count(needle)==1,'Reviewed unmount timeout fix missing or ambiguous'
old=fn.replace(needle,'dpolicy->granularity = 1;\n#ifdef CONFIG_OPLUS_FEATURE_OF2FS').replace('__init_discard_policy','old_policy')
preamble=r"""
#include <stdbool.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
#define DEF_MAX_DISCARD_REQUEST 8
#define MAX_PLIST_NUM 32
#define DEF_MIN_DISCARD_ISSUE_TIME 50
#define DEF_MID_DISCARD_ISSUE_TIME 500
#define DEF_MAX_DISCARD_ISSUE_TIME 60000
#define DEF_DISCARD_URGENT_UTIL 80
#define DEF_URGENT_DISCARD_ISSUE_TIME 10
#define DEF_DISCARD_EMPTY_ISSUE_TIME 5000
#define SM_I(s) (s)
#define utilization(s) ((s)->util)
#define atomic_read(p) (*(p))
enum {DPOLICY_BG,DPOLICY_FORCE,DPOLICY_FSTRIM,DPOLICY_UMOUNT,DPOLICY_BALANCE,DPOLICY_PERFORMANCE};
struct discard_cmd_control {int discard_cmd_cnt;};
struct f2fs_sb_info {struct discard_cmd_control *dcc_info;int util;};
struct discard_policy {int type;bool sync,ordered;unsigned granularity;int max_requests,io_aware_gran;bool timeout,io_busy;int min_interval,mid_interval,max_interval;bool io_aware;};
"""
main=r"""
int main(void) {
 int count=0;
 for(int policy=0;policy<6;policy++) for(int util=0;util<=100;util+=20)
 for(int pending=0;pending<2;pending++) for(unsigned gran=1;gran<=32;gran*=2) {
  struct discard_cmd_control dcc={pending};struct f2fs_sb_info sbi={&dcc,util};
  struct discard_policy a={0},b={0};
  old_policy(&sbi,&a,policy,gran);__init_discard_policy(&sbi,&b,policy,gran);
#ifdef CONFIG_OPLUS_FEATURE_OF2FS
  if(policy==DPOLICY_UMOUNT) {assert(!a.timeout);assert(b.timeout);a.timeout=true;}
#endif
  assert(memcmp(&a,&b,sizeof(a))==0);
  if(policy==DPOLICY_UMOUNT) {assert(b.timeout);assert(!b.io_aware);assert(b.granularity==1);}
  count++;
 }
 printf("PASS %d discard policy cases\n",count);return 0;
}
"""
results=[]
with tempfile.TemporaryDirectory(prefix='f2fs-policy-') as work:
 src=Path(work)/'policy.c';src.write_text(preamble+old+fn+main)
 for of2fs in (False,True):
  exe=Path(work)/('policy.exe' if os.name=='nt' else 'policy')
  cmd=[os.environ.get('CC','gcc'),'-std=c99','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)]
  if of2fs:cmd.append('-DCONFIG_OPLUS_FEATURE_OF2FS')
  subprocess.run(cmd,check=True);out=subprocess.check_output([str(exe)],text=True).strip();results.append({'of2fs':of2fs,'result':out});print(of2fs,out)
if a.report:Path(a.report).write_text(json.dumps({'tests':results,'hardware_tested':False},indent=2)+'\n')

#!/usr/bin/env python3
"""Compile and exercise actual vendor selection functions, without hardware."""
import argparse,json,re,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('kernel',type=Path);p.add_argument('modules',type=Path)
p.add_argument('--baseline',type=Path);p.add_argument('--report',type=Path)
a=p.parse_args(); rel='vendor/oplus/kernel/vibrator/aw8697_haptic/aw8697.c'
new=(a.modules/rel).read_text()
old=a.baseline.read_text() if a.baseline else subprocess.check_output(['git','-C',str(a.modules),'show','HEAD:'+rel],text=True)
display=(a.kernel/'techpack/display/msm/dsi/dsi_panel.c').read_text()
def function(s,signature):
 start=s.index(signature);return s[start:s.index('\n}',start)+2]
def arrays(s):
 return dict(re.findall(r'static char (aw8697_rtp_name\w*)\[\]\[AW8697_RTP_NAME_MAX\]\s*=\s*(\{.*?\n\};)',s,re.S))
before,after=arrays(old),arrays(new);assert before.keys()==after.keys()
for name in before:
 b=re.findall(r'"([^"]+)"',before[name]);n=re.findall(r'"([^"]+)"',after[name]);assert len(b)==len(n)
 for i,(x,y) in enumerate(zip(b,n)):
  if name=='aw8697_rtp_name_1815_170Hz' and i in (110,111,112):
   assert x=='aw8697_reserved_%d.bin'%i
   assert y=='aw8697_fingerprint_effect%d_RTP_%d.bin'%(i-109,i)
  else: assert x==y,(name,i)
haptic=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define pr_err(...) ((void)0)
struct firmware { int unused; };
struct aw8697 { int device_id,f0,rtp_file_num,rtp_routine_on; void *dev; };
static char requested[64]; static int fail; static struct firmware firmware;
static int request_firmware(const struct firmware **out,const char *name,void *dev) {
 (void)dev; strcpy(requested,name); *out=&firmware; return fail ? -1 : 0;
}
'''
for prefix,s in [('old_',old),('new_',new)]:
 chunk='\n'.join('static char %s[][64] = %s'%(name,body) for name,body in arrays(s).items())
 chunk+='\n'+function(s,'const struct firmware *aw8697_rtp_request_firmware(struct aw8697 *aw8697)')
 chunk=re.sub(r'\baw8697_rtp_name\w*\b',lambda m:prefix+m[0],chunk)
 haptic+=chunk.replace('aw8697_rtp_request_firmware(',prefix+'request(')+'\n'
haptic+=r'''
int main(void) {
 int ids[]={815,81538,1815,9595,619,1040,832,999};
 int fs[]={1400,1470,1471,1525,1526,1670,1671,1680,1681,1720,1721,1725,1726,1751,2280,2281,2320,2321,2350,2351};
 unsigned cases=0;
 for(unsigned d=0;d<8;d++) for(unsigned f=0;f<20;f++)
 for(int i=0;i<(ids[d]==1815 ? 436 : 300);i++) for(fail=0;fail<2;fail++) {
  struct aw8697 a={ids[d],fs[f],i,1,NULL},b=a; char previous[64],expected[64];
  const struct firmware *ra=old_request(&a); strcpy(previous,requested);
  const struct firmware *rb=new_request(&b);
  assert(ra==rb && a.rtp_routine_on==b.rtp_routine_on);
#ifdef CONFIG_OPLUS_HAPTIC_OOS
  if(ids[d]==1815 && i>=110 && i<=112) {
   snprintf(expected,sizeof(expected),"aw8697_fingerprint_effect%d_RTP_%d.bin",i-109,i);
   assert(!strcmp(requested,expected));
  } else
#endif
   assert(!strcmp(previous,requested));
  cases++;
 }
 printf("PASS haptic: %u selection/failure cases\n",cases);
}
'''
helper=function(display,'static bool dsi_panel_amb655x_skip_display_off(')
start=display.index('\tif (!rc &&\n\t    panel->cur_mode->priv_info->cmd_sets[DSI_CMD_POST_ON_BACKLIGHT].count)')
backlight=display[start:display.index('\n\tset_oplus_display_power_status',start)]
assert 'if (dsi_panel_amb655x_skip_display_off(panel, type, cmds, count)) {\n\t\tcmds++;\n\t\tcount--;\n\t}' in display
aod=r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char u8; typedef unsigned int u32;
enum dsi_cmd_set_type {DSI_CMD_SET_LP1,DSI_CMD_SET_NOLP,DSI_CMD_POST_ON_BACKLIGHT,OTHER};
enum {SDE_MODE_DPMS_ON,SDE_MODE_DPMS_LP1,SDE_MODE_DPMS_LP2,OFF};
#define MIPI_DSI_DCS_SHORT_WRITE 5
#define MIPI_DCS_SET_DISPLAY_OFF 0x28
struct dsi_cmd_desc {struct {int type,tx_len;const void *tx_buf;} msg;};
struct dsi_panel_cmd_set {struct dsi_cmd_desc *cmds;u32 count;};
struct priv {struct dsi_panel_cmd_set cmd_sets[4];};
struct mode {struct priv *priv_info;};
struct dsi_panel {int power_mode;struct {const char *vendor_name;} oplus_priv;bool need_power_on_backlight;struct mode *cur_mode;};
'''+helper+'\nstatic void finish(struct dsi_panel *panel,int rc) {panel->need_power_on_backlight=true;\n'+backlight+r'''
}
int main(void) {
 unsigned cases=0;
 for(int vendor=0;vendor<2;vendor++) for(int power=0;power<4;power++)
 for(int type=0;type<4;type++) for(int count=0;count<4;count++) for(int v=0;v<6;v++) {
  u8 data=v==1 ? 0x29 : 0x28;
  struct dsi_cmd_desc cmd={{v==2 ? 0x39 : 5,v==3 ? 2 : 1,v==4 ? NULL : &data}};
  struct dsi_cmd_desc *cmds=v==5 ? NULL : &cmd;
  struct priv priv={0};struct mode mode={&priv};
  struct dsi_panel p={power,{vendor ? "OTHER" : "AMB655X"},true,&mode};
  bool expected=!vendor && count>1 && v==0 && ((type==DSI_CMD_SET_LP1 && power==SDE_MODE_DPMS_ON) || (type==DSI_CMD_SET_NOLP && (power==SDE_MODE_DPMS_LP1 || power==SDE_MODE_DPMS_LP2)));
  assert(dsi_panel_amb655x_skip_display_off(&p,type,cmds,count)==expected);
  priv.cmd_sets[DSI_CMD_SET_LP1]=(struct dsi_panel_cmd_set){cmds,count};
  for(int post=0;post<2;post++) for(int failure=0;failure<2;failure++) {
   priv.cmd_sets[DSI_CMD_POST_ON_BACKLIGHT].count=post;finish(&p,failure ? -1 : 0);
   assert(p.need_power_on_backlight==!(!failure && post && !vendor && power==SDE_MODE_DPMS_ON && count>1 && v==0));cases++;
  }
 }
 printf("PASS AOD: %u transition/guard/backlight cases\n",cases);
}
'''
compiler=shutil.which('cc') or shutil.which('gcc');assert compiler
results=[]
with tempfile.TemporaryDirectory(prefix='kebab-regression-') as temp:
 for name,code,flags in [('haptic-oos',haptic,['-DCONFIG_OPLUS_HAPTIC_OOS']),('haptic-other',haptic,[]),('aod',aod,[])]:
  source=Path(temp)/(name+'.c');binary=Path(temp)/(name+'.exe');source.write_text(code)
  subprocess.run([compiler,'-std=c99','-O2',*flags,str(source),'-o',str(binary)],check=True)
  result=subprocess.check_output([str(binary)],text=True).strip();print(result);results.append(name+': '+result)
if a.report:
 a.report.parent.mkdir(parents=True,exist_ok=True)
 a.report.write_text(json.dumps({'tests':results,'hardware_tested':False},indent=2)+'\n')

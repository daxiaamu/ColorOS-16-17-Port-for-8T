#!/usr/bin/env python3
"""Compile actual S3908 decoding code and regression-test all firmware event IDs."""
from pathlib import Path
import argparse, re, shutil, subprocess, tempfile
p = argparse.ArgumentParser()
p.add_argument('modules', type=Path)
p.add_argument('--baseline', type=Path)
a = p.parse_args()
rel = 'vendor/oplus/kernel/touchpanel/oplus_touchscreen/'
chip = rel + 'Synaptics/Syna_tcm_oncell/'
new = (a.modules / chip / 'synaptics_tcm_oncell.c').read_text()
old = a.baseline.read_text() if a.baseline else subprocess.check_output(
    ['git', '-C', str(a.modules), 'show', 'HEAD:' + chip + 'synaptics_tcm_oncell.c'], text=True)
def decoder(s, name):
    start = s.index('static int syna_get_gesture_info(')
    end = s.index('\n}', start) + 2
    return s[start:end].replace('syna_get_gesture_info(', name + '(')
headers = (a.modules / chip / 'synaptics_tcm_oncell.h').read_text() + '\n' + (a.modules / rel / 'touchpanel_common.h').read_text()
defines = '\n'.join(line for line in headers.splitlines() if re.match(r'^#define\s+\w+\s+(?:0x[0-9a-fA-F]+|[0-9]+)\s*(?://.*)?$', line))
code = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define TPD_INFO(...) ((void)0)
#define TPD_DEBUG(...) ((void)0)
struct point { int x,y; };
struct gesture_info { int gesture_type,clockwise; struct point Point_start,Point_end,Point_1st,Point_2nd,Point_3rd,Point_4th; };
struct touch_data { unsigned int lpwg_gesture; unsigned char extra_gesture_info[8],data_point[24]; };
struct touch_hcd { struct touch_data touch_data; };
struct syna_tcm_data { struct touch_hcd *touch_hcd; };
''' + defines + '\n' + decoder(old, 'original_decode') + '\n' + decoder(new, 'patched_decode') + r'''
int main(void) {
    struct touch_hcd touch = {0};
    struct syna_tcm_data chip = {&touch};
    for (unsigned int id=0; id<256; ++id) {
        for (unsigned int sample=0; sample<4; ++sample) {
            struct gesture_info before={0},after={0};
            memset(&touch,0,sizeof(touch));
            touch.touch_data.lpwg_gesture=id;
            for (int i=0;i<24;++i) touch.touch_data.data_point[i]=(unsigned char)(i+sample*19);
            touch.touch_data.extra_gesture_info[0]=0x34;
            touch.touch_data.extra_gesture_info[1]=0x02;
            touch.touch_data.extra_gesture_info[2]=(unsigned char[]){0x10,0x20,0x04,0x08}[sample];
            touch.touch_data.extra_gesture_info[3]=0x06;
            touch.touch_data.extra_gesture_info[4]=(unsigned char[]){0x41,0x42,0x44,0x48}[sample];
            assert(original_decode(&chip,&before)==0);
            assert(patched_decode(&chip,&after)==0);
            if (id==STAP_DETECT || id==DTAP_DETECT) {
                assert(after.gesture_type==(id==STAP_DETECT ? SingleTap : DouTap));
                assert(after.Point_start.x==0x234);
                assert(after.Point_start.y==(0x600 | touch.touch_data.extra_gesture_info[2]));
                if (id==STAP_DETECT) assert(before.gesture_type==UnkownGesture);
            } else {
                assert(memcmp(&before,&after,sizeof(before))==0);
            }
        }
    }
    puts("PASS: 1024 cases; single/double tap coordinates correct; all other event decoding unchanged");
    return 0;
}
'''
compiler = shutil.which('cc') or shutil.which('gcc')
assert compiler, 'A host C compiler is required'
with tempfile.TemporaryDirectory(prefix='s3908-gesture-') as d:
    source=Path(d)/'test.c'; binary=Path(d)/'test.exe'
    source.write_text(code)
    subprocess.run([compiler,'-std=c99','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
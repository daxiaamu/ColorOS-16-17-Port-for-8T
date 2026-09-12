#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,os,shutil,subprocess,urllib.request,zipfile
R=Path(__file__).resolve().parent; S=json.loads((R/'sources.json').read_text()); C=json.loads((R/'manager-compatibility.json').read_text())
D=Path('manager-output'); D.mkdir(); T=Path('official-manager-download'); T.mkdir()
run_id=S['official_manager_run_id']
# Validate exact upstream source pairing before downloading anything.
headers={'User-Agent':'ColorOS8T-ReSukiSU-build','Accept':'application/vnd.github+json'}
if os.environ.get('GH_TOKEN'): headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
req=urllib.request.Request(f'https://api.github.com/repos/ReSukiSU/ReSukiSU/actions/runs/{run_id}',headers=headers)
with urllib.request.urlopen(req,timeout=30) as f: run=json.load(f)
assert run['head_sha']==S['resukisu_commit'] and run['conclusion']=='success'
assert run['event']!='pull_request','Do not use ephemeral PR-signing builds'
try:
 subprocess.run(['gh','run','download',str(run_id),'--repo','ReSukiSU/ReSukiSU','--name',S['official_manager_artifact'],'--dir',str(T)],check=True,timeout=180)
except (subprocess.CalledProcessError,subprocess.TimeoutExpired):
 # Anonymous mirror of the SAME immutable official Actions artifact, never latest.
 url=f'https://nightly.link/ReSukiSU/ReSukiSU/actions/runs/{run_id}/{S["official_manager_artifact"]}.zip'
 subprocess.run(['curl','-fL','--retry','3',url,'-o',str(T/'artifact.zip')],check=True)
 with zipfile.ZipFile(T/'artifact.zip') as z:
  candidates=[n for n in z.namelist() if Path(n).name==S['official_manager_apk']]
  assert len(candidates)==1
  (T/S['official_manager_apk']).write_bytes(z.read(candidates[0]))
files=list(T.rglob(S['official_manager_apk'])); assert len(files)==1
apk=files[0]; assert hashlib.sha256(apk.read_bytes()).hexdigest()==S['official_manager_sha256']
sdk=Path(os.environ.get('ANDROID_HOME','/usr/local/lib/android/sdk'))
tools=sorted(sdk.glob('build-tools/*/apksigner')); assert tools,'Android apksigner is required'
result=subprocess.run([str(tools[-1]),'verify','--verbose','--print-certs',str(apk)],check=True,capture_output=True,text=True)
assert C['official_certificate_sha256'] in result.stdout
assert 'Verified using v2 scheme (APK Signature Scheme v2): true' in result.stdout
shutil.copyfile(apk,D/S['official_manager_apk'])
(D/'apk-verification.txt').write_text(result.stdout)
(D/'provenance.json').write_text(json.dumps({'official_run':run['html_url'],'source_commit':run['head_sha'],'apk_sha256':S['official_manager_sha256'],'recompiled':False,'resigned':False,'matches_supplied_telegram_apk':True},indent=2)+'\n')
print('Official Actions APK verified against source commit, full-file SHA256 and official signing certificate')

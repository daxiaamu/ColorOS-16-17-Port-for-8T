#!/usr/bin/env python3
"""Resolve one official main-branch build and preserve its verified APK/source pair."""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, zipfile
from artifact_names import artifact_names

REPO = 'ReSukiSU/ReSukiSU'
APK_NAME = re.compile(r'ReSukiSU_(v[0-9][A-Za-z0-9.-]*)_([0-9]+)-arm64-v8a-release\.apk')

def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/'+REPO+'/'+path], text=True, timeout=60))

def eligible(run):
    return (run.get('name') == 'Build Manager' and run.get('head_branch') == 'main'
            and run.get('event') in ('push', 'workflow_dispatch')
            and run.get('status') == 'completed' and run.get('conclusion') == 'success'
            and run.get('head_repository', {}).get('full_name') == REPO)

def latest_run():
    # GitHub returns runs newest first. Scan pages, never select a PR/fork build.
    for page in range(1, 11):
        runs = api(f'actions/runs?branch=main&status=success&per_page=100&page={page}')['workflow_runs']
        candidates = [r for r in runs if eligible(r)]
        if candidates:
            return max(candidates, key=lambda r: (r['created_at'], r['id']))
        if len(runs) < 100:
            break
    raise RuntimeError('No successful official main-branch Build Manager run found')

def release_artifact(run):
    artifacts = []
    for page in range(1, 11):
        rows = api(f'actions/runs/{run["id"]}/artifacts?per_page=100&page={page}')['artifacts']
        artifacts.extend(rows)
        if len(rows) < 100:
            break
    matches = [a for a in artifacts if a['name'] == 'Manager-release']
    assert len(matches) == 1 and not matches[0]['expired'], 'Latest Manager-release missing/expired; refusing older fallback'
    return matches[0]

def extract_apk(archive, target):
    with zipfile.ZipFile(archive) as z:
        names = [n for n in z.namelist() if APK_NAME.fullmatch(Path(n).name)]
        assert len(names) == 1, 'Expected exactly one official arm64 release APK'
        assert z.testzip() is None, 'Corrupt official artifact archive'
        out = target / Path(names[0]).name
        out.write_bytes(z.read(names[0]))
        return out

def verify_signer(output, expected):
    digests = re.findall(r'^(?:Signer #\d+|V2 Signer:) certificate SHA-256 digest: ([0-9a-fA-F]+)$', output, re.M)
    assert digests == [expected], 'Official APK signer changed; review required'
    assert 'Verified using v2 scheme (APK Signature Scheme v2): true' in output

def sdk_tool(name):
    sdk = Path(os.environ.get('ANDROID_HOME', '/usr/local/lib/android/sdk'))
    suffix = '.bat' if os.name == 'nt' and name == 'apksigner' else '.exe' if os.name == 'nt' else ''
    candidates = sorted(sdk.glob('build-tools/*/'+name+suffix))
    assert candidates, f'Android SDK {name} is required'
    return str(candidates[-1])

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--latest', action='store_true')
    p.add_argument('--output-root', type=Path, default=Path('.'))
    args = p.parse_args()
    root = Path(__file__).resolve().parent
    sources = json.loads((root/'sources.json').read_text())
    trust = json.loads((root/'manager-compatibility.json').read_text())
    out = args.output_root
    download = out/'official-manager-download'; download.mkdir(parents=True)
    manager = out/'manager-output'; manager.mkdir()
    lock = out/'resolved-inputs'; lock.mkdir()
    run = latest_run() if args.latest else api(f'actions/runs/{sources["official_manager_run_id"]}')
    assert eligible(run), 'Only successful official main branch builds are accepted'
    if not args.latest:
        assert run['head_sha'] == sources['resukisu_commit']
    artifact = release_artifact(run)
    # Download the selected immutable artifact only. The mirror uses the same run ID.
    archive = download/'artifact.zip'
    command = ['gh','api',f'repos/{REPO}/actions/artifacts/{artifact["id"]}/zip']
    try:
        with archive.open('wb') as f:
            subprocess.run(command, stdout=f, check=True, timeout=180)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        subprocess.run(['curl','-fL','--retry','3','--connect-timeout','30','--max-time','180',
                        f'https://nightly.link/{REPO}/actions/runs/{run["id"]}/Manager-release.zip',
                        '-o',str(archive)], check=True, timeout=600)
    apk = extract_apk(archive, download)
    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    if not args.latest:
        assert apk.name == sources['official_manager_apk'] and digest == sources['official_manager_sha256']
    verification = subprocess.check_output([sdk_tool('apksigner'),'verify','--verbose','--print-certs',str(apk)], text=True)
    verify_signer(verification, trust['official_certificate_sha256'])
    badging = subprocess.check_output([sdk_tool('aapt'),'dump','badging',str(apk)], text=True)
    version, code = APK_NAME.fullmatch(apk.name).groups()
    assert re.search(r"versionCode='"+re.escape(code)+r"'", badging), 'APK versionCode differs from filename'
    apk_version = re.search(r"versionName='([^']+)'", badging).group(1)
    assert apk_version.lstrip('v') == version.lstrip('v'), 'APK versionName differs from filename'
    assert re.search(r"native-code:.*'arm64-v8a'", badging), 'APK missing arm64 native code'
    sources.update(resukisu_commit=run['head_sha'], official_manager_run_id=run['id'],
                   official_manager_artifact='Manager-release', official_manager_artifact_id=artifact['id'],
                   official_manager_apk=apk.name, official_manager_sha256=digest)
    names = artifact_names(sources=sources)
    compatibility = {
        'official_certificate_sha256': trust['official_certificate_sha256'],
        'official_certificate_size': trust['official_certificate_size'],
        'apk_signature_scheme': 'v2 verified by apksigner',
        'verified_apk': apk.name, 'verified_apk_sha256': digest,
        'official_actions_run': run['html_url'], 'official_actions_artifact': 'Manager-release',
        'resukisu_commit': run['head_sha'], 'runtime_device_validation': 'pending',
        'temporary_PR_signing_keys': 'not accepted'}
    for filename, value in [('sources.json',sources), ('manager-compatibility.json',compatibility)]:
        (lock/filename).write_text(json.dumps(value,indent=2)+'\n')
    shutil.copyfile(apk, manager/names['apk'])
    (manager/'apk-verification.txt').write_text(verification)
    (manager/'provenance.json').write_text(json.dumps({
        'output_filename': names['apk'], 'original_filename': apk.name, 'build_date': names['build_date'],
        'official_run': run['html_url'], 'official_artifact_id': artifact['id'],
        'source_commit': run['head_sha'], 'apk_sha256': digest, 'recompiled': False, 'resigned': False,
        'matches_supplied_telegram_apk': digest == '04dfe68cdce7d1284f52f4953ffde9403f03243804fde56a5b739d920b230d82'
    },indent=2)+'\n')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as f:
            for key in ('prefix','build_date'):
                f.write(f'{key}={names[key]}\n')
    print(json.dumps({'run':run['html_url'],'commit':run['head_sha'], 'names':names},indent=2))

if __name__ == '__main__':
    main()
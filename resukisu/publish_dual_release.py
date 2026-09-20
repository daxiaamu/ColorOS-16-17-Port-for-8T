#!/usr/bin/env python3
"""Validate both ROM products and their shared official APK before draft upload."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,zipfile
from artifact_names import artifact_names

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def verify(root):
    root=Path(root)
    def one(pattern):
        found=list(root.rglob(pattern));assert len(found)==1,(pattern,found)
        return found[0]
    lock=json.loads((root/'resolved-resukisu-inputs/sources.json').read_text())
    assert lock==json.loads((root/'kernel/sources.json').read_text())
    apk=one('*_arm64-v8a-release.apk')
    provenance=json.loads((apk.parent/'provenance.json').read_text())
    assert provenance['source_commit']==lock['resukisu_commit']
    assert not provenance['recompiled'] and not provenance['resigned']
    assert sha(apk)==lock['official_manager_sha256']
    assets=[apk];records=[]
    for rom in ('ColorOS16','ColorOS17'):
        boot=one('*_'+rom+'_kebab_boot.img');twrp=one('*_'+rom+'_kebab_TWRP.zip')
        manifest=json.loads((twrp.parent/'manifest.json').read_text())
        assert manifest['rom']==rom and manifest['source_locks']==lock
        assert manifest['rom_profile']['rom']==rom
        assert manifest['accepted_boot_sha256']==[row['sha256'] for row in manifest['rom_profile']['boots']]
        for row in manifest['rom_profile']['boots']:
            assert row['preserved_components']==manifest['preserved_components']
            assert row['bytes']==lock['boot_partition_bytes']
        names=artifact_names(provenance['build_date'],sources=lock,rom=rom)
        assert manifest['artifact_names']==names
        assert [boot.name,twrp.name,apk.name]==[names['boot'],names['twrp'],names['apk']]
        assert sha(boot)==manifest['boot_sha256'] and boot.stat().st_size==lock['boot_partition_bytes']
        with zipfile.ZipFile(twrp) as z:
            assert z.testzip() is None
            assert json.loads(z.read('manifest.json'))==manifest
            assert hashlib.sha256(z.read('images/boot.img')).hexdigest()==sha(boot)
            installer=z.read('META-INF/com/google/android/update-binary').decode()
            expected="ACCEPTED_HASHES='"+manifest['accepted_boot_sha256'][0]+' '+' '.join(manifest['accepted_boot_sha256'][1:])+"'"
            assert expected in installer and ('ReSukiSU for '+rom) in installer
        for line in (twrp.parent/'SHA256SUMS.txt').read_text().splitlines():
            digest,name=line.split('  ',1);assert Path(name).name==name
            assert sha(boot if name==boot.name else twrp.parent/name)==digest
        records.append(manifest);assets.extend([boot,twrp])
    assert set(records[0]['accepted_boot_sha256']).isdisjoint(records[1]['accepted_boot_sha256'])
    return assets

if __name__=='__main__':
    assets=verify(sys.argv[1]);print('Verified ColorOS16 + ColorOS17 and shared official manager')
    if '--verify-only' not in sys.argv:
        subprocess.run(['gh','release','upload',os.environ['RELEASE_TAG'],*[str(p) for p in assets],'--clobber'],check=True)

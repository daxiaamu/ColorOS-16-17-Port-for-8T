"""Only permit reviewed boot hashes with identical preserved components."""
import json,re
from pathlib import Path

def compatible_hashes(path, components, partition_bytes):
    data=json.loads(Path(path).read_text())
    assert data['schema']==1, 'Unknown boot compatibility schema'
    hashes=[]
    for item in data['boots']:
        digest=item['sha256']
        assert re.fullmatch(r'[0-9a-f]{64}',digest), 'Invalid compatible boot hash'
        assert item['bytes']==partition_bytes, 'Compatible boot partition size differs'
        assert item['preserved_components']==components, 'Compatible boot components differ from packaging base'
        assert digest not in hashes, 'Duplicate compatible boot'
        hashes.append(digest)
    return hashes

"""Hash-locked edits to named smali methods. Outputs changed sources, never flashes."""
import argparse, hashlib, json, re, shutil, tempfile
from pathlib import Path, PurePosixPath

def sha(data):
    return hashlib.sha256(data).hexdigest()

def safe_path(root, name):
    if not isinstance(name,str) or not name or '\\' in name or ':' in name:
        raise ValueError('Expected relative POSIX smali path')
    rel=PurePosixPath(name)
    if rel.is_absolute() or '..' in rel.parts or str(rel)!=name or rel.suffix!='.smali':
        raise ValueError('Invalid smali path')
    path=root.joinpath(*rel.parts)
    path.resolve().relative_to(root.resolve())
    return path

def edit_method(text, edit):
    signature=edit['method']
    matches=list(re.finditer(r'(?m)^\.method[^\r\n]*[ \t]'+re.escape(signature)+r'[ \t]*\r?$',text))
    if len(matches)!=1:
        raise ValueError('Method must match once: '+signature)
    start=matches[0].end()
    end_match=re.search(r'(?m)^\.end method[ \t]*\r?$',text[start:])
    if end_match is None: raise ValueError('Unterminated method')
    end=start+end_match.start(); body=text[start:end]
    before,after=edit['before'],edit['after'];count=edit.get('count',1)
    if type(count)!=int or count<1: raise ValueError('Invalid count')
    if not before or before==after or body.count(before)!=count:
        raise ValueError('Unexpected instructions: '+signature)
    if '.method' in after or '.end method' in after:
        raise ValueError('Method boundary injection unsupported')
    return text[:start]+body.replace(before,after)+text[end:]

def apply_plan(source, plan, output):
    source=Path(source).resolve();output=Path(output).absolute()
    if output.exists(): raise ValueError('Output must not exist')
    if not source.is_dir(): raise ValueError('Source directory missing')
    if output.resolve()==source or source in output.resolve().parents:
        raise ValueError('Output must be outside source')
    if plan.get('schema')!=1 or not plan.get('files'): raise ValueError('Invalid plan')
    prepared=[];seen=set()
    for item in plan['files']:
        name=item['path'];path=safe_path(source,name)
        if name in seen: raise ValueError('Duplicate input')
        seen.add(name);data=path.read_bytes();expected=item['sha256']
        if not re.fullmatch('[0-9a-f]{64}',expected) or sha(data)!=expected:
            raise ValueError('Input hash mismatch: '+name)
        text=data.decode('utf-8')
        if not item.get('edits'): raise ValueError('Empty edits')
        for edit in item['edits']: text=edit_method(text,edit)
        changed=text.encode('utf-8')
        if changed==data: raise ValueError('No change')
        if item.get('output_sha256') and sha(changed)!=item['output_sha256']:
            raise ValueError('Output hash mismatch')
        prepared.append((name,changed,sha(data)))
    # Validate every input before writing any output; source remains immutable.
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.smali-stage-',dir=str(output.parent)))
    try:
        records=[]
        for name,data,old_hash in prepared:
            target=safe_path(stage,name);target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            records.append({'path':name,'input_sha256':old_hash,'output_sha256':sha(data)})
        report={'schema':1,'state':'patched-source-only','files':records}
        (stage/'patch-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        if output.exists(): raise ValueError('Output appeared during preflight')
        stage.rename(output)
        return report
    finally:
        if stage.exists(): shutil.rmtree(stage)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('plan',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    try: report=apply_plan(a.source,json.loads(a.plan.read_text(encoding='utf-8-sig')),a.output)
    except (ValueError,KeyError,TypeError,OSError) as e: p.exit(2,str(e)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()

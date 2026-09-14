import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/coloros-port-8t/scripts'))
from patch_smali import apply_plan,sha

class PatchTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.root=Path(t.name);self.src=self.root/'source';self.src.mkdir();self.out=self.root/'output'
        self.data=b'.class public Lexample/Config;\n.super Ljava/lang/Object;\n.method public getLimit()I\n    .registers 1\n    const/16 v0, 0xa\n    return v0\n.end method\n'
        (self.src/'Config.smali').write_bytes(self.data)
        self.plan={'schema':1,'files':[{'path':'Config.smali','sha256':sha(self.data),'edits':[{'method':'getLimit()I','before':'const/16 v0, 0xa','after':'const/16 v0, 0x32'}]}]}
    def test_success_source_immutable(self):
        r=apply_plan(self.src,self.plan,self.out)
        self.assertEqual((self.src/'Config.smali').read_bytes(),self.data)
        self.assertIn('0x32',(self.out/'Config.smali').read_text())
        self.assertEqual(r['files'][0]['output_sha256'],sha((self.out/'Config.smali').read_bytes()))
    def test_hash_mismatch(self):
        self.plan['files'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):apply_plan(self.src,self.plan,self.out)
        self.assertFalse(self.out.exists())
    def test_all_files_preflight(self):
        bad=copy.deepcopy(self.plan['files'][0]);bad['path']='Other.smali';bad['sha256']='0'*64
        (self.src/'Other.smali').write_bytes(self.data);self.plan['files'].append(bad)
        with self.assertRaises(ValueError):apply_plan(self.src,self.plan,self.out)
        self.assertFalse(self.out.exists())
    def test_missing_method(self):
        self.plan['files'][0]['edits'][0]['method']='different()I'
        with self.assertRaises(ValueError):apply_plan(self.src,self.plan,self.out)
    def test_ambiguous_method(self):
        data=self.data+self.data;(self.src/'Config.smali').write_bytes(data)
        self.plan['files'][0]['sha256']=sha(data)
        with self.assertRaises(ValueError):apply_plan(self.src,self.plan,self.out)
    def test_escape(self):
        for path in ['../outside.smali','/absolute.smali','C:/outside.smali','a\\b.smali']:
            self.plan['files'][0]['path']=path
            with self.assertRaises(ValueError):apply_plan(self.src,self.plan,self.out)
    def test_overwrite_refused(self):
        self.out.mkdir();(self.out/'keep').write_text('keep')
        with self.assertRaises(ValueError):apply_plan(self.src,self.plan,self.out)
        self.assertEqual((self.out/'keep').read_text(),'keep')
    def test_source_output_refused(self):
        with self.assertRaises(ValueError):apply_plan(self.src,self.plan,self.src/'changed')
    def test_replay_refused(self):
        apply_plan(self.src,self.plan,self.out)
        with self.assertRaises(ValueError):apply_plan(self.out,self.plan,self.root/'twice')
    def test_output_hash_checked(self):
        self.plan['files'][0]['output_sha256']='0'*64
        with self.assertRaises(ValueError):apply_plan(self.src,self.plan,self.out)
    def test_duplicate_refused(self):
        self.plan['files'].append(copy.deepcopy(self.plan['files'][0]))
        with self.assertRaises(ValueError):apply_plan(self.src,self.plan,self.out)
if __name__=='__main__':unittest.main()

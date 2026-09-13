import copy, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
from fetch_official_manager import eligible, latest_run, release_artifact, extract_apk, verify_signer
from artifact_names import artifact_names

class OfficialBuildTests(unittest.TestCase):
    def setUp(self):
        self.run={'name':'Build Manager','head_branch':'main','event':'push','status':'completed',
                  'conclusion':'success','head_repository':{'full_name':'ReSukiSU/ReSukiSU'},
                  'created_at':'2026-09-13T00:00:00Z','id':42}
    def test_exclude_untrusted_and_failed_runs(self):
        self.assertTrue(eligible(self.run))
        for key,value in [('event','pull_request'),('head_branch','weblate-main'),('conclusion','failure'),
                          ('status','in_progress'),('head_repository',{'full_name':'fork/ReSukiSU'}),('name','Lints Check')]:
            other=dict(self.run);other[key]=value;self.assertFalse(eligible(other))
    def test_latest_not_first_unrelated_run(self):
        older=dict(self.run,id=41,created_at='2026-09-12T00:00:00Z')
        pr=dict(self.run,id=43,event='pull_request')
        with patch('fetch_official_manager.api',return_value={'workflow_runs':[pr,older,self.run]}):
            self.assertEqual(latest_run()['id'],42)
    def test_expired_latest_fails_instead_of_falling_back(self):
        with patch('fetch_official_manager.api',return_value={'artifacts':[{'name':'Manager-release','expired':True}]}):
            with self.assertRaises(AssertionError):release_artifact(self.run)
    def test_signer_must_be_exact_and_v2_valid(self):
        expected='ab'*32
        good='Signer #1 certificate SHA-256 digest: '+expected+'\nVerified using v2 scheme (APK Signature Scheme v2): true\n'
        verify_signer(good,expected)
        verify_signer(good.replace("Signer #1", "V2 Signer:"),expected)
        for bad in [good.replace(expected,'cd'*32),good.replace(': true',': false'),good+'Signer #2 certificate SHA-256 digest: '+expected+'\n']:
            with self.assertRaises(AssertionError):verify_signer(bad,expected)
    def test_archive_uses_only_arm64_release_and_no_path_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);archive=p/'test.zip';name='ReSukiSU_v4.2.0-rc1_35137-arm64-v8a-release.apk'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('../../'+name,b'arm64');z.writestr('other-armeabi.apk',b'arm')
            result=extract_apk(archive,p)
            self.assertEqual(result,p/name);self.assertEqual(result.read_bytes(),b'arm64')
            with zipfile.ZipFile(archive,'a') as z:z.writestr('duplicate/'+name,b'other')
            with self.assertRaises(AssertionError):extract_apk(archive,p)
    def test_names_use_resolved_version(self):
        names=artifact_names('20260913',sources={'official_manager_apk':'ReSukiSU_v4.2.0-rc1_35137-arm64-v8a-release.apk'})
        self.assertEqual(names['prefix'],'ReSukiSU_v4.2.0-rc1_35137_20260913')

if __name__=='__main__':unittest.main()
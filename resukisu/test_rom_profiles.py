#!/usr/bin/env python3
import json,unittest
from pathlib import Path
from artifact_names import artifact_names
from boot_compatibility import compatible_hashes
R=Path(__file__).resolve().parent
class Profiles(unittest.TestCase):
    def test_separate_rom_names_and_shared_apk(self):
        a=artifact_names('20260921',rom='ColorOS16');b=artifact_names('20260921',rom='ColorOS17')
        self.assertNotEqual(a['boot'],b['boot']);self.assertNotEqual(a['twrp'],b['twrp']);self.assertEqual(a['apk'],b['apk'])
        with self.assertRaises(ValueError):artifact_names(rom='ColorOS18')
    def test_reviewed_profiles_preserve_components_and_do_not_overlap(self):
        profiles=[json.loads((R/'profiles'/(rom+'.json')).read_text()) for rom in ('ColorOS16','ColorOS17')]
        parts=profiles[0]['boots'][0]['preserved_components'];accepted=[]
        for profile in profiles:
            accepted.append(set(compatible_hashes(R/'profiles'/(profile['rom']+'.json'),parts,100663296)))
        self.assertTrue(accepted[0].isdisjoint(accepted[1]))
        self.assertIn('bdd8967199778d244d908e1adc8b5a85e614fdbd47db59df642ad0c7b29a0751',accepted[0])
        self.assertEqual(accepted[1],{'d8ee22c0ea67dace2214e502327652d97162d4f5817bcb4819318cd55da323f6'})
    def test_refuse_changed_base_component(self):
        path=R/'profiles/ColorOS17.json';parts=json.loads(path.read_text())['boots'][0]['preserved_components'];parts['ramdisk.cpio']='0'*64
        with self.assertRaises(AssertionError):compatible_hashes(path,parts,100663296)
if __name__=='__main__':unittest.main()

"""Only synthetic ARSC: no original binaries, values or IDs."""
import struct
import unittest
from a1_resource_package_rename import InvalidResourceTable,package_names,rewrite_exact_namespace,classify_outer_signing_change,only_expected_own_v1_signing_changes

ORIG="ru.yandex.music"
CLONE="pro.celikom.yandex.nativeclonelab"

def minimal_table(name=ORIG,payload=b"stable resource bytes"):
    encoded=name.encode("utf-16le")
    pkg=struct.pack("<HHI",0x0200,288,288+len(payload))
    pkg+=struct.pack("<I",0x7f)
    pkg+=encoded+b"\0"*(256-len(encoded))
    pkg+=b"\0"*20
    assert len(pkg)==288
    pkg+=payload
    return struct.pack("<HHII",0x0002,12,12+len(pkg),1)+pkg

class SyntheticTests(unittest.TestCase):
    def test_only_package_name_changes(self):
        original=minimal_table()
        clone=rewrite_exact_namespace(original,ORIG,CLONE)
        self.assertEqual(package_names(original),(ORIG,))
        self.assertEqual(package_names(clone),(CLONE,))
        self.assertEqual(len(original),len(clone))
        self.assertEqual(original[:24],clone[:24])
        self.assertEqual(original[-20:],clone[-20:])
        self.assertNotEqual(original,clone)
    def test_never_rewrite_unknown_or_damaged(self):
        for data in (b"",b"invalid",minimal_table()[:35],
                     minimal_table("unrelated")):
            with self.assertRaises(InvalidResourceTable):
                rewrite_exact_namespace(data,ORIG,CLONE)
    def test_outer_signing_classification_private_bounded(self):
        examples = {
            "META-INF/MANIFEST.MF":"V1_MANIFEST",
            "META-INF/OWN-KEY.SF":"V1_SIGNATURE_FILE",
            "META-INF/OWN-KEY.RSA":"V1_SIGNATURE_BLOCK",
            "META-INF/OWN-KEY.EC":"V1_SIGNATURE_BLOCK",
            "META-INF/OWN-KEY.DSA":"V1_SIGNATURE_BLOCK",
            "META-INF/subdir/OWN-KEY.RSA":"OTHER_META_INF",
            "META-INF/other.txt":"OTHER_META_INF",
            "assets/inner.apk":"NON_META_INF_APP_CONTENT",
            "classes.dex":"NON_META_INF_APP_CONTENT",
            "resources.arsc":"NON_META_INF_APP_CONTENT",
        }
        for name, expected in examples.items():
            self.assertEqual(classify_outer_signing_change(name), expected)

    def test_only_three_exact_own_signature_members_are_exempt(self):
        own=["META-INF/MANIFEST.MF","META-INF/OWN-KEY.SF",
             "META-INF/OWN-KEY.RSA"]
        self.assertTrue(only_expected_own_v1_signing_changes(own))
        self.assertTrue(only_expected_own_v1_signing_changes(list(reversed(own))))
        invalid=[
            own[:2],
            own+["assets/inner.apk"],
            own[:2]+["assets/classes.dex"],
            ["META-INF/MANIFEST.MF","META-INF/OWN-KEY.SF",
             "META-INF/OTHER.RSA"],
            ["META-INF/MANIFEST.MF","META-INF/OWN-KEY.SF",
             "META-INF/OWN-KEY.SF"],
            ["META-INF/other.MF","META-INF/OWN-KEY.SF",
             "META-INF/OWN-KEY.RSA"]
        ]
        for names in invalid:
            self.assertFalse(only_expected_own_v1_signing_changes(names))

    def test_no_double_patch(self):
        result=rewrite_exact_namespace(minimal_table(),ORIG,CLONE)
        with self.assertRaises(InvalidResourceTable):
            rewrite_exact_namespace(result,ORIG,CLONE)

if __name__=="__main__":unittest.main()

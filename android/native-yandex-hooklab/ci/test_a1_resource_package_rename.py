"""Only synthetic ARSC: no original binaries, values or IDs."""
import struct
import unittest
from a1_resource_package_rename import InvalidResourceTable,package_names,rewrite_exact_namespace

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
    def test_no_double_patch(self):
        result=rewrite_exact_namespace(minimal_table(),ORIG,CLONE)
        with self.assertRaises(InvalidResourceTable):
            rewrite_exact_namespace(result,ORIG,CLONE)

if __name__=="__main__":unittest.main()

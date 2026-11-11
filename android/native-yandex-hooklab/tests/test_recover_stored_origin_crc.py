"""Synthetic ZIP CRC recovery contract. No third-party APK, network or device."""
import io
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from recover_stored_origin_crc import HOST, rewrite_only_if_origin_crc_mismatch

class CrcRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
    def input_zip(self, corrupt=True):
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w") as z:
            z.writestr("classes.dex", b"original-dex")
        src = self.dir / "patched.apk"
        with zipfile.ZipFile(src, "w") as z:
            z.writestr("classes.dex", b"loader-stub")
            z.writestr(HOST, inner.getvalue(), compress_type=zipfile.ZIP_STORED)
            z.writestr("assets/lspatch/config.json", b'{"sigBypassLevel":0}')
        if corrupt:
            data = bytearray(src.read_bytes())
            central = data.find(b"PK\x01\x02")
            hits = 0
            while central >= 0:
                n = int.from_bytes(data[central+28:central+30],"little")
                name = data[central+46:central+46+n]
                if name == HOST.encode():
                    data[central+16:central+20] = b"\x01\x02\x03\x04"
                    hits += 1
                central = data.find(b"PK\x01\x02",central+4)
            assert hits == 1
            src.write_bytes(data)
        return src,inner.getvalue()
    def test_corrects_only_incorrect_stored_crc(self):
        src, origin = self.input_zip()
        with zipfile.ZipFile(src) as z:
            with self.assertRaises(zipfile.BadZipFile):
                z.read(HOST)
        dest=self.dir/"fixed.apk"
        result=rewrite_only_if_origin_crc_mismatch(src,dest)
        self.assertTrue(result["crc_repaired"])
        with zipfile.ZipFile(dest) as z:
            self.assertEqual(z.read(HOST),origin)
            self.assertEqual(z.read("classes.dex"),b"loader-stub")
            self.assertIn(b'"sigBypassLevel":0',z.read("assets/lspatch/config.json"))
    def test_overlapping_directory_layout_repacked_even_when_crc_matches(self):
        src,origin=self.input_zip(corrupt=False)
        original_read=zipfile.ZipFile.read
        def simulate_overlap(zf, name, *args, **kwargs):
            n = name.filename if isinstance(name, zipfile.ZipInfo) else name
            if zf.filename == str(src) and n == HOST:
                raise zipfile.BadZipFile("Overlapped entries: Possible zip bomb")
            return original_read(zf,name,*args,**kwargs)
        dest=self.dir/"repaired-overlap.apk"
        with patch.object(zipfile.ZipFile,"read",simulate_overlap):
            result=rewrite_only_if_origin_crc_mismatch(src,dest)
        self.assertTrue(result["layout_repacked"])
        self.assertFalse(result["crc_repaired"])
        self.assertEqual(result["repacked_reason"],"OVERLAPPING_DIRECTORY_LAYOUT")
        with zipfile.ZipFile(dest) as z:
            self.assertEqual(z.read(HOST),origin)

    def test_keeps_page_alignment_of_stored_lspatch_elf_assets(self):
        # Real loader is 4-ABI. Synthetic ELF contains header fields only.
        src, inner = self.input_zip(corrupt=True)
        with zipfile.ZipFile(src,"a") as z:
            for abi,machine,klass in (
                    ("armeabi-v7a",40,1),("arm64-v8a",183,2),
                    ("x86",3,1),("x86_64",62,2)):
                elf=bytearray(20)
                elf[:4]=b"\x7fELF"
                elf[4]=klass
                elf[18:20]=machine.to_bytes(2,"little")
                z.writestr("assets/lspatch/so/"+abi+"/liblspatch.so",
                           bytes(elf),compress_type=zipfile.ZIP_STORED)
        dest=self.dir/"repaired-with-elf.apk"
        result=rewrite_only_if_origin_crc_mismatch(src,dest)
        self.assertTrue(result["layout_repacked"])
        with zipfile.ZipFile(dest) as z, dest.open("rb") as fh:
            self.assertEqual(z.read(HOST),inner)
            for abi in ("armeabi-v7a","arm64-v8a","x86","x86_64"):
                info=z.getinfo("assets/lspatch/so/"+abi+"/liblspatch.so")
                fh.seek(info.header_offset)
                header=fh.read(30)
                name_len=int.from_bytes(header[26:28],"little")
                extra_len=int.from_bytes(header[28:30],"little")
                data_start=info.header_offset+30+name_len+extra_len
                self.assertEqual(data_start%4096,0,abi)

    def test_rejects_double_repair_and_new_destination_collision(self):
        src,_=self.input_zip(corrupt=False)
        dest=self.dir/"fixed.apk"
        result=rewrite_only_if_origin_crc_mismatch(src,dest)
        self.assertFalse(result["crc_repaired"])
        self.assertFalse(dest.exists())
        with self.assertRaisesRegex(ValueError,"NEW_SEPARATE_OUTPUT"):
            rewrite_only_if_origin_crc_mismatch(src,src)
    def test_corruption_in_other_member_must_fail(self):
        src,_=self.input_zip()
        b=bytearray(src.read_bytes())
        # Last outer central-directory record: avoid a nested ZIP signature.
        p=b.rfind(b"PK\x01\x02")
        b[p+16:p+20]=b"\xff\xff\xff\xff"
        src.write_bytes(b)
        with self.assertRaisesRegex(ValueError,"UNRELATED_APK_ENTRY"):
            rewrite_only_if_origin_crc_mismatch(src,self.dir/"invalid.apk")

if __name__ == "__main__":
    unittest.main()

import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

MODULE = Path(__file__).resolve().parents[1] / "floki-extension-owner-consumer.py"
spec = importlib.util.spec_from_file_location("owner_extension_consumer", MODULE)
consumer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consumer)


def archive(version="0.4.82", api="https://api.celikom.com",
            perms=None, update_url=False, bad_path=None):
    if perms is None:
        perms = ["https://music.yandex.ru/*", "https://api.celikom.com/*"]
    manifest = {"manifest_version": 3, "version": version, "host_permissions": perms}
    if update_url:
        manifest["update_url"] = "https://untrusted.invalid/updates.xml"
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as z:
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("api/config.json", json.dumps({"baseUrl": api}))
        if bad_path is not None:
            z.writestr(bad_path, "malicious")
    return output.getvalue()


class OwnerPublisherTests(unittest.TestCase):
    def test_version_sort_not_lexicographic(self):
        self.assertLess(consumer.ver("0.4.9"), consumer.ver("0.4.82"))
        self.assertLess(consumer.ver("0.4.82"), consumer.ver("0.4.100"))

    def test_reject_version_path_traversal(self):
        for value in ("0.4.82/evil", "../0.4.82", "0.04.82", "0.4.82.zip", ""):
            with self.subTest(value=value):
                with self.assertRaises(RuntimeError):
                    consumer.ver(value)

    def test_valid_extension_package(self):
        consumer.check_zip(archive(), "0.4.82")

    def test_wrong_origin_or_manifest_rejected(self):
        bad = [
            archive(version="0.4.81"),
            archive(api="https://old.example.invalid"),
            archive(perms=["<all_urls>"]),
            archive(update_url=True),
            archive(bad_path="../escape")
        ]
        for data in bad:
            with self.subTest(index=bad.index(data)):
                with self.assertRaises(RuntimeError):
                    consumer.check_zip(data, "0.4.82")

    def test_reject_duplicate_archive_entries(self):
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("manifest.json", "{}")
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                z.writestr("manifest.json", "{}")
        with self.assertRaises(RuntimeError):
            consumer.check_zip(out.getvalue(), "0.4.82")

    def test_withdrawn_owner_release_is_noop(self):
        from unittest.mock import patch
        with patch.object(consumer, "root_dir"), \
             patch.object(consumer, "trusted_approvals", return_value={}), \
             patch.object(consumer.os, "open", side_effect=AssertionError("MUST_NOT_PUBLISH")):
            consumer.main()

    def test_sha256_stable(self):
        self.assertEqual(consumer.digest(b"abc"),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


if __name__ == "__main__":
    unittest.main()

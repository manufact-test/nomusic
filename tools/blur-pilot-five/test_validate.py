import copy
import json
from pathlib import Path
import unittest
import validate


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(validate.MANIFEST.read_text(encoding="utf-8"))
        self.tracks = validate.validate_manifest(self.manifest)

    def test_five_pinned_candidates(self):
        self.assertEqual([t["track_id"] for t in self.tracks], ["17198343", "24442524", "27323567", "29851850", "32988400"])

    def test_duplicate_candidate_is_rejected(self):
        bad = copy.deepcopy(self.manifest)
        bad["tracks"][1]["track_id"] = bad["tracks"][0]["track_id"]
        with self.assertRaises(ValueError):
            validate.validate_manifest(bad)

    def test_sixth_candidate_rejected(self):
        bad = copy.deepcopy(self.manifest)
        bad["tracks"].append(copy.deepcopy(bad["tracks"][0]))
        with self.assertRaises(ValueError):
            validate.validate_manifest(bad)

    def test_bad_sha_rejected(self):
        bad = copy.deepcopy(self.manifest)
        bad["tracks"][0]["source_blob_sha1"] = "not-a-sha"
        with self.assertRaises(ValueError):
            validate.validate_manifest(bad)

    def test_approved_catalog_dedupe(self):
        snapshot = {"schema": 1, "source": "celikom_owner_catalog_snapshot", "complete": True, "total_tracks": 1, "tracks": [{"track_id": "17198343", "title": "Опять сегодня"}]}
        self.assertEqual(validate.compare_approved_snapshot(self.tracks, snapshot)["exact_duplicates"], ["17198343"])

    def test_same_title_new_id_reported(self):
        snapshot = {"schema": 1, "source": "celikom_owner_catalog_snapshot", "complete": True, "total_tracks": 1, "tracks": [{"track_id": "99", "title": "Лошадка"}]}
        self.assertEqual(validate.compare_approved_snapshot(self.tracks, snapshot)["same_title_other_id"][0]["candidate_id"], "32988400")

    def test_incomplete_catalog_rejected(self):
        snapshot = {"schema": 1, "source": "celikom_owner_catalog_snapshot", "complete": False, "total_tracks": 0, "tracks": []}
        with self.assertRaises(ValueError):
            validate.compare_approved_snapshot(self.tracks, snapshot)


if __name__ == "__main__":
    unittest.main()
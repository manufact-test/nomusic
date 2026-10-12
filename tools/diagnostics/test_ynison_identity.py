import unittest
from ynison_identity import observe


def frame(identity="141103805"):
    return {"activeDeviceIdOptional": "phone", "devices": [{"info": {"deviceId": "phone"}}],
            "playerState": {"playerQueue": {"currentPlayableIndex": 0,
                "playableList": [{"playableType": "TRACK", "playableId": identity,
                                  "albumIdOptional": "37458189", "privateToken": "secret"}]},
                "status": {"paused": False, "progressMs": "90000"}}, "authorization": "secret"}


class IdentityTests(unittest.TestCase):
    def test_ids_do_not_depend_on_celikom_catalog_or_titles(self):
        for identity in ("141103805", "38436680", "48592132", "123456789"):
            result = observe(frame(identity), "phone", 10000, 10001)
            self.assertEqual(identity, result["candidate_track_id"])
            self.assertFalse(result["exact_track_id_verified"])
            self.assertFalse(result["replacement_started"])
            self.assertNotIn("secret", str(result))

    def test_wrong_device_missing_device_or_ambiguous_device_cannot_select(self):
        self.assertNotIn("candidate_track_id", observe(frame(), "laptop", 0, 0))
        for devices in ([], [{"info": {"deviceId": "phone"}, "isOffline": True}],
                        [{"info": {"deviceId": "phone"}}] * 2):
            data = frame(); data["devices"] = devices
            self.assertNotIn("candidate_track_id", observe(data, "phone", 0, 0))
        self.assertEqual("target_device_unbound", observe(frame(), "", 0, 0)["status"])

    def test_invalid_index_injection_radio_and_local_track_are_rejected(self):
        for index in (-1, 1, True, "0"):
            data=frame(); data["playerState"]["playerQueue"]["currentPlayableIndex"]=index
            self.assertNotIn("candidate_track_id", observe(data,"phone",0,0))
        for kind in (0, 2, 3, 4, "LOCAL_TRACK", True, 1.0):
            data=frame(); data["playerState"]["playerQueue"]["playableList"][0]["playableType"]=kind
            self.assertNotIn("candidate_track_id",observe(data,"phone",0,0))
        data=frame();data["playerState"]["playerQueueInjectOptional"]={"playable": {"playableType": "AD"}}
        self.assertEqual("injected_content_active", observe(data,"phone",0,0)["status"])

    def test_age_and_non_numeric_ids_are_rejected(self):
        for now in (-1,5001):
            self.assertEqual("observation_stale",observe(frame(),"phone",0,now)["status"])
        self.assertIn("candidate_track_id",observe(frame(),"phone",0,5000))
        for identity in ("0", "12:34", "opaque", "123?token=secret", None):
            self.assertNotIn("candidate_track_id",observe(frame(identity),"phone",0,0))


if __name__ == "__main__":
    unittest.main()

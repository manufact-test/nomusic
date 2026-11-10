import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_native_shared_caller_bridge import (
    upstream_depths, shared_caller_proximity, joined_graph_findings, sink_family,
    media_session_api_family, media_session_callsite_census
)

def M(symbol):
    return ("L"+symbol+";", "a", "()V")


class SharedCallerBridgeTests(unittest.TestCase):
    def test_shared_siblings_recovered_without_direct_path(self):
        root, source, media = M("root"), M("src"), M("player")
        reverse = {source: {root}, media: {root}}
        self.assertEqual(upstream_depths(reverse, {source}), {source: 0, root: 1})
        report = shared_caller_proximity(reverse, {source}, {media})
        self.assertEqual(report["shared_callers_within_bounded_depth"], 1)
        self.assertEqual(report["lowest_sum_of_call_distances"], 2)
        self.assertFalse(report["first_bounded_hints"][0]
                         ["current_audio_source_or_decoder_proven"])

    def test_no_path_not_a_negative_decoder_proof(self):
        report = shared_caller_proximity({}, {M("one")}, {M("two")})
        self.assertEqual(report["shared_callers_within_bounded_depth"], 0)
        self.assertIsNone(report["lowest_sum_of_call_distances"])

    def test_bounded_multi_hop_ancestor(self):
        root, middle, src, media = M("root"), M("middle"), M("src"), M("player")
        reverse = {src:{middle}, middle:{root}, media:{root}}
        r=shared_caller_proximity(reverse,{src},{media},3)
        self.assertEqual(r["lowest_sum_of_call_distances"],3)
        self.assertEqual(r["first_bounded_hints"][0]["fileinfo_call_depth"],2)
        self.assertEqual(r["first_bounded_hints"][0]["media_call_depth"],1)

    def test_completely_unrelated_common_manager_is_non_authoritative(self):
        common, src, media = M("manager"),M("a"),M("b")
        result = shared_caller_proximity({src:{common},media:{common}},
                                          {src},{media})
        self.assertEqual(result["interpretation"],
                         "INVOKE_PROXIMITY_ONLY_NO_REGISTER_VALUE_FLOW")
        self.assertNotIn("trackId", str(result))

    def test_actual_obfuscated_media3_owners_not_random_classes(self):
        self.assertEqual(sink_family(("Lfxc;","a","()V")),
                         "media3_interface_or_obfuscated_implementor")
        self.assertEqual(sink_family(("Landroid/media/AudioTrack;","play","()V")),
                         "android_framework_media")
        self.assertIsNone(sink_family(("Lged;","a","()V")))
        self.assertIsNone(sink_family(("Lcom/yandex/analytics/State;","a","()V")))

    def test_cross_dex_method_triples_joined(self):
        src, middle, audio = M("swSource"), M("bridge"), ("Lfxc;","a","()V")
        d1={"complete":True,"defined_method_bodies":2,"invoke_edges":1,
            "_source_methods":{"converter_caller":{src},"model_consumer":set()},
            "_reverse_edges":{src:{middle}}}
        d2={"complete":True,"defined_method_bodies":2,"invoke_edges":1,
            "_source_methods":{"converter_caller":set(),"model_consumer":set()},
            "_reverse_edges":{audio:{middle}}}
        res=joined_graph_findings([d1,d2])
        group=res["method_proximity"]["media3_interface_or_obfuscated_implementor"]
        self.assertEqual(group["converter_callers"]["shared_callers_within_bounded_depth"],1)
        self.assertFalse(res["real_decoder_proven"])
        self.assertEqual(res["converter_caller_count"], 1)
        self.assertEqual(res["direct_converter_caller_hints"], ["LswSource;->a"])
        self.assertFalse(res["source_callsite_audio_flow_proven"])
        self.assertFalse(res["replacement_audio_played_in_native_android"])

    def test_negative_or_large_search_guarded(self):
        with self.assertRaises(ValueError):
            upstream_depths({}, {M("source")}, depth=7)
        with self.assertRaises(ValueError):
            upstream_depths({M("a"):{M("b")}}, {M("a")}, cap=1)

    def test_platform_session_exact_signatures_only(self):
        self.assertEqual(media_session_api_family((
            "Landroid/media/session/MediaSession;",
            "setMetadata", "(Landroid/media/MediaMetadata;)V")),
            "exact_android_framework_observer_methods")
        self.assertEqual(media_session_api_family((
            "Landroid/media/session/MediaSession;",
            "setPlaybackState", "(Landroid/media/session/PlaybackState;)V")),
            "exact_android_framework_observer_methods")
        self.assertIsNone(media_session_api_family((
            "Landroid/media/session/MediaSession;",
            "setPlaybackState", "(Ljava/lang/Object;)V")))
        self.assertEqual(media_session_api_family((
            "Landroid/support/v4/media/session/MediaSessionCompat;",
            "setPlaybackState", "(Labc;)V")), "media_session_compat_methods")
        self.assertIsNone(media_session_api_family((
            "Landroidx/media3/session/MediaSession;", "update", "()V")))

    def test_non_authoritative_platform_session_counts(self):
        exact=("Landroid/media/session/MediaSession;",
               "setMetadata","(Landroid/media/MediaMetadata;)V")
        reverse={exact:{M("caller"),M("caller2")},
                 ("Landroid/media/session/MediaSession;",
                  "setPlaybackState", "(Landroid/media/session/PlaybackState;)V"):
                  {M("caller2")}}
        census=media_session_callsite_census(reverse)
        platform=census["exact_android_framework_observer_methods"]
        self.assertEqual(platform["unique_direct_caller_methods"],2)
        self.assertFalse(platform["runtime_media_session_callback_proven"])
        self.assertEqual(platform["per_method"]["setMetadata"]["unique_caller_methods"],2)
        self.assertEqual(platform["per_method"]["setPlaybackState"]["unique_caller_methods"],1)


if __name__ == "__main__":
    unittest.main()

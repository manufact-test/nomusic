import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_postfileinfo_lifecycle import (
    merge_reverse,reverse_to_forward,bounded_path_to_media,
    consumer_summary,downstream_consumer_telemetry
)


def M(owner,name="a",sig="()V"):
    return ("L"+owner+";",name,sig)


class SignedPostFileinfoLifecycleTests(unittest.TestCase):
    def test_six_dex_reverse_merge_joins_exact_triples(self):
        dto=M("div","b","()Lod5;")
        c1=M("consumerA")
        c2=M("consumerB")
        scans=[
            {"complete":True,"_reverse_edges":{dto:{c1}}},
            {"complete":True,"_reverse_edges":{dto:{c2}}},
        ]
        merged=merge_reverse(scans)
        self.assertEqual(merged[dto],{c1,c2})
        f=reverse_to_forward(merged)
        self.assertIn(dto,f[c1])
        self.assertIn(dto,f[c2])

    def test_reaching_media_method_call_not_dataflow_proof(self):
        dto=M("div","f","()Ls3p;")
        caller=M("consumer")
        player=("Lfxc;","a","()V")
        forward={caller:{dto,player},dto:set()}
        result=bounded_path_to_media(forward,{caller})
        self.assertEqual(result["first_media_proximity_paths"][0]["hop_count"],1)
        self.assertFalse(result["first_media_proximity_paths"][0]
                         ["register_source_flow_proven"])
        self.assertFalse(result["decoder_proven"])

    def test_no_false_positive_if_unrelated(self):
        dto=M("div","f","()Ls3p;")
        caller=M("consumer")
        result=bounded_path_to_media({caller:{dto}},{caller})
        self.assertEqual(result["first_media_proximity_paths"],[])
        self.assertFalse(result["search_truncated"])

    def test_bad_depth_or_seed_count_rejected(self):
        with self.assertRaises(ValueError):
            bounded_path_to_media({},set(),depth=7)
        with self.assertRaises(ValueError):
            bounded_path_to_media({},set(),depth=-1)

    def test_dto_consumer_census_is_not_player_claim(self):
        dto=M("div","c","()Lr68;")
        src=M("consumer")
        reverse={dto:{src}}
        result,trace=downstream_consumer_telemetry(reverse,{})
        self.assertEqual(result["direct_dto_consumer_method_count"],1)
        self.assertEqual(trace["direct_consumer_methods"],1)
        self.assertFalse(trace["consumer_methods_are_register_bound_to_coroutine_l_div"])
        self.assertEqual(trace["bounded_consumer_to_media_callgraph_proximity"]
                         ["first_media_proximity_paths"],[])

    def test_next_typed_jgv_consumer_is_not_implicitly_decoder(self):
        model=("Ljgv;","a","()Ljava/lang/Object;")
        owner=M("nextConsumer")
        report,trace=downstream_consumer_telemetry({model:{owner}},{},"Ljgv;")
        self.assertEqual(report["direct_dto_consumer_method_count"],1)
        self.assertEqual(trace["consumer_owner_examples"],["LnextConsumer;"])
        self.assertFalse(trace["bounded_consumer_to_media_callgraph_proximity"]
                         ["decoder_proven"])

    def test_reject_incomplete_dex(self):
        with self.assertRaises(ValueError):
            merge_reverse([{"complete":False}])


if __name__=="__main__":
    unittest.main()

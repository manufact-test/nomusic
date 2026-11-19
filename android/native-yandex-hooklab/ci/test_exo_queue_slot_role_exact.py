#!/usr/bin/env python3
"""Fail-closed scoped native ExoPlayer queue-slot audit fixtures."""
import unittest
from exo_queue_slot_role_exact import QUEUE, HOLDER, ENGINE, slot_field, direct_getter

class StubDex:
    def __init__(self): self.fields={3:(QUEUE,"hidden_a",HOLDER),4:(QUEUE,"hidden_b",HOLDER)}
    def __repr__(self): return "StubDex"
    def method(self, idx): raise AssertionError("not used")

class SlotRoleTests(unittest.TestCase):
    def test_typed_field_only(self):
        from exo_queue_slot_role_exact import audit
        old=audit.field_id
        audit.field_id=lambda d,i: (QUEUE,"internal",HOLDER) if i==3 else ("LX;","other",HOLDER)
        try:
            self.assertEqual(slot_field(StubDex(),0x54,[0x10,3]),(QUEUE,"internal",HOLDER))
            self.assertIsNone(slot_field(StubDex(),0x54,[0x10,4]))
            self.assertIsNone(slot_field(StubDex(),0x55,[0x10,3]))
        finally: audit.field_id=old

    def test_no_false_current_on_unrelated_return(self):
        from exo_queue_slot_role_exact import audit
        old=audit.field_id
        audit.field_id=lambda d,i: (QUEUE,"hidden_a",HOLDER)
        try:
            s={(QUEUE,"hidden_a",HOLDER):"SLOT_A"}
            self.assertEqual(direct_getter([(0,0x54,[0x0,3]),(1,0x11,[0x0])],StubDex(),s),"SLOT_A")
            self.assertEqual(direct_getter([(0,0x54,[0x0,3]),(1,0x11,[0x0100])],StubDex(),s),None)
            # iget A=v1; return-object v1 -> identical direct field
            self.assertEqual(direct_getter([(0,0x54,[0x0100,3]),(1,0x11,[0x0100])],StubDex(),s),"SLOT_A")
            # branch destroys the direct proof
            self.assertIsNone(direct_getter([(0,0x54,[0x0100,3]),(1,0x32,[0]),(2,0x11,[0x0100])],StubDex(),s))
        finally: audit.field_id=old

class SignedSlotBWriterCensusTests(unittest.TestCase):
    def test_exact_five_sites_only(self):
        from exo_queue_slot_role_exact import (SIGNED_SLOT_B_DIRECT_WRITES,
            validate_signed_slot_b_direct_writes)
        proven=validate_signed_slot_b_direct_writes(list(SIGNED_SLOT_B_DIRECT_WRITES))
        self.assertEqual(proven["publisher_base_direct_iput_object_site_count"],5)
        self.assertTrue(proven["bounded_exact_site_proven"])
        self.assertFalse(proven["currently_selected_track_or_queue_epoch_proven"])
        self.assertFalse(proven["reflective_or_native_mutations_excluded"])

    def test_extra_missing_duplicate_and_pc_drift_fail_closed(self):
        from exo_queue_slot_role_exact import (SIGNED_SLOT_B_DIRECT_WRITES,
            validate_signed_slot_b_direct_writes)
        sites=list(SIGNED_SLOT_B_DIRECT_WRITES)
        for altered in (
            sites[:-1],
            sites+[sites[0]],
            sites+[(QUEUE,"unexpected","()V",999)],
            [(*sites[0][:3],sites[0][3]+1)]+sites[1:],
        ):
            with self.subTest(altered=altered):
                with self.assertRaisesRegex(ValueError,"QUEUE_SIGNED_SLOT_B_DIRECT_WRITES_CHANGED"):
                    validate_signed_slot_b_direct_writes(altered)

class SignedSlotBProvenanceTests(unittest.TestCase):
    """Tiny synthetic DEX instructions: no publisher method values in tests."""
    def _w(self,op,val,receiver):
        return (receiver<<12)|(val<<8)|op

    def _fixture(self):
        from exo_queue_slot_role_exact import QUEUE,HOLDER,ENGINE
        w=self._w
        # Fake IDs are arbitrary. Field names are synthetic, not private.
        fields={1:(QUEUE,"a",HOLDER),2:(QUEUE,"b",HOLDER),
                3:(QUEUE,"c",HOLDER),4:(QUEUE,"d",HOLDER),
                5:(HOLDER,"next",HOLDER),6:(QUEUE,"other","I"),
                7:(HOLDER,"different",HOLDER)}
        scripts={
            1:{305:(0x5b,(w(0x5b,3,2),1)),
               307:(0x5b,(w(0x5b,3,2),2)),
               309:(0x5b,(w(0x5b,3,2),3)),
               311:(0x5b,(w(0x5b,15,2),6)),
               313:(0x5b,(w(0x5b,3,2),4)),
               652:(0x54,(w(0x54,3,9),2)),
               654:(0x71,(0x71,1,0)),
               657:(0x54,(w(0x54,3,3),5)),
               659:(0x5b,(w(0x5b,3,9),2))},
            2:{0:(0x54,(w(0x54,0,3),1)),
               6:(0x54,(w(0x54,2,3),2)),
               8:(0x33,(w(0x33,0,2),6)),
               10:(0x54,(w(0x54,2,0),5)),
               12:(0x5b,(w(0x5b,2,3),2)),
               49:(0x54,(w(0x54,0,3),1)),
               51:(0x54,(w(0x54,0,0),5)),
               53:(0x5b,(w(0x5b,0,3),1))},
            3:{19:(0x54,(w(0x54,0,2),2)),
               21:(0x33,(w(0x33,3,0),9)),
               23:(0x54,(w(0x54,0,2),1)),
               25:(0x5b,(w(0x5b,0,2),2))},
            4:{30:(0x12,(0x0012,)),
               31:(0x5b,(w(0x5b,0,3),1)),
               33:(0x5b,(w(0x5b,0,3),4)),
               35:(0x5b,(w(0x5b,0,3),2)),
               37:(0x5b,(w(0x5b,0,3),3))},
        }
        stub=object()
        targets={
            ENGINE:(stub,0,1),
            (QUEUE,"if","()Lxh6;"):(stub,0,2),
            (QUEUE,"while","(Lxh6;)I"):(stub,0,3),
            (QUEUE,"for","()V"):(stub,0,4),
        }
        slots={fields[i]:"SLOT_"+letter for i,letter in
               ((1,"A"),(2,"B"),(3,"C"),(4,"D"))}
        return scripts,fields,targets,slots

    def _prove(self,scripts,fields,targets,slots):
        from exo_queue_slot_role_exact import (
            verify_signed_slot_b_local_provenance,audit)
        from unittest.mock import patch
        with patch.object(audit,"instructions",
                side_effect=lambda _dex,off: [
                    (pc,op,w) for pc,(op,w) in scripts[off].items()]), \
             patch.object(audit,"field_id",
                side_effect=lambda _dex,index: fields[index]):
            return verify_signed_slot_b_local_provenance(targets,slots)

    def test_five_source_categories_without_epoch_claim(self):
        scripts,fields,targets,slots=self._fixture()
        result=self._prove(scripts,fields,targets,slots)
        self.assertEqual(
            [row["origin"] for row in result["exact_writer_local_reference_origin_categories"]],
            ["INITIAL_SAME_HOLDER_REFERENCE",
             "OLD_SLOT_B_HOLDER_SUCCESSOR",
             "FRONT_HOLDER_SUCCESSOR_CONDITIONAL",
             "SLOT_A_REFERENCE_CONDITIONAL",
             "ZERO_NULL_REFERENCE"])
        self.assertFalse(result["whole_program_queue_epoch_proven"])
        self.assertFalse(result["runtime_selected_edition_proven"])

    def test_wrong_branch_field_register_successor_and_zero_fail_closed(self):
        base,fields,targets,slots=self._fixture()
        from copy import deepcopy
        variants=[]
        w=self._w
        for scope,pc,replacement in (
            (1,307,(0x5b,(w(0x5b,1,2),2))),
            (1,657,(0x54,(w(0x54,3,3),7))),
            (2,8,(0x33,(w(0x33,0,2),7))),
            (2,12,(0x5b,(w(0x5b,1,3),2))),
            (3,23,(0x54,(w(0x54,0,2),3))),
            (4,30,(0x12,(0x1012,))),
        ):
            changed=deepcopy(base);changed[scope][pc]=replacement
            variants.append((scope,pc,changed))
        for scope,pc,changed in variants:
            with self.subTest(scope=scope,pc=pc):
                with self.assertRaisesRegex(ValueError,"SLOT_B_PROVENANCE_"):
                    self._prove(changed,fields,targets,slots)

class SignedPeriodTokenTests(unittest.TestCase):
    def test_mutable_holder_info_not_promoted_to_selected_epoch(self):
        from exo_queue_slot_role_exact import (
            SIGNED_PERIOD_TOKEN_WRITERS,validate_signed_period_token_writers)
        rows={alias:list(writes) for alias,writes in SIGNED_PERIOD_TOKEN_WRITERS.items()}
        witness=validate_signed_period_token_writers(rows)
        self.assertEqual(witness["holder_period_info_direct_writers"],8)
        self.assertEqual(witness["period_info_id_direct_writers"],1)
        self.assertEqual(witness["period_id_long_direct_writers"],1)
        self.assertTrue(witness["same_holder_cannot_be_assumed_same_period_info"])
        self.assertFalse(witness["original_selected_edition_or_queue_epoch_proven"])
        self.assertFalse(witness["reflection_or_native_mutations_excluded"])

    def test_fail_closed_when_any_member_writer_drifted(self):
        from exo_queue_slot_role_exact import (
            SIGNED_PERIOD_TOKEN_WRITERS,validate_signed_period_token_writers)
        original={alias:list(writes) for alias,writes in SIGNED_PERIOD_TOKEN_WRITERS.items()}
        from copy import deepcopy
        bad=[]
        for category in original:
            gone=deepcopy(original);gone[category].pop();bad.append(gone)
            duplicate=deepcopy(original);duplicate[category].append(duplicate[category][0]);bad.append(duplicate)
            extra=deepcopy(original);extra[category].append(("Lfake;","unexpected","()V",999));bad.append(extra)
            offset=deepcopy(original)
            first=offset[category][0];offset[category][0]=(*first[:3],first[3]+1)
            bad.append(offset)
        wrong_category=deepcopy(original);wrong_category["unverified"]=[]
        bad.append(wrong_category)
        for i,case in enumerate(bad):
            with self.subTest(i=i):
                with self.assertRaisesRegex(ValueError,"QUEUE_PERIOD_TOKEN_"):
                    validate_signed_period_token_writers(case)

class SignedInfoRefreshTests(unittest.TestCase):
    def _scenario(self):
        from exo_queue_slot_role_exact import (
            SIGNED_PERIOD_INFO_REFRESH,SIGNED_PERIOD_INFO_CLONE,
            PERIOD_INFO,PERIOD_ID,HOLDER)
        holder_field=(HOLDER,"synthetic_info",PERIOD_INFO)
        id_field=(PERIOD_INFO,"synthetic_id",PERIOD_ID)
        class Dex:
            def method(self,index):
                if index==1:return SIGNED_PERIOD_INFO_CLONE
                if index==2:return (
                    PERIOD_INFO,"<init>","(LSl6$b;JJJJZZZZZ)V")
                raise AssertionError("unexpected method index")
        owner=Dex(); info=Dex()
        scripts={
            1:[
                (56,0x54,(0x1a54,10)),
                (64,0x6e,(0x306e,1,0x098a)),
                (67,0x0c,(0x080c,)),
                (68,0x5b,(0x185b,10)),
            ],
            2:[
                (15,0x54,(0x0354,11)),
                (33,0x76,(0x0f76,2,2)),
            ],
        }
        targets={
            SIGNED_PERIOD_INFO_REFRESH:(owner,0,1),
            SIGNED_PERIOD_INFO_CLONE:(info,0,2),
        }
        return scripts,targets,holder_field,id_field

    def _check(self,scripts,targets,holder_field,id_field):
        from exo_queue_slot_role_exact import (
            verify_signed_period_info_refresh_preserves_id,audit)
        from unittest.mock import patch
        with patch.object(audit,"instructions",
                side_effect=lambda _dex,offset:scripts[offset]), \
             patch.object(audit,"field_id",
                side_effect=lambda _dex,index: {
                    10:holder_field,11:id_field}[index]):
            return verify_signed_period_info_refresh_preserves_id(
                targets,holder_field,id_field)

    def test_same_id_ref_may_survive_original_period_info_refresh(self):
        scripts,targets,hf,pf=self._scenario()
        proof=self._check(scripts,targets,hf,pf)
        self.assertTrue(proof["refreshed_period_info_can_retain_same_java_period_id"])
        self.assertTrue(proof["same_period_id_not_sufficient_as_monotonic_queue_epoch"])
        self.assertFalse(proof["currently_selected_edition_or_queue_generation_proven"])

    def test_refresh_wrong_method_result_or_token_register_fails_closed(self):
        scripts,targets,hf,pf=self._scenario()
        from copy import deepcopy
        variants=[]
        for section,pc,replacement in (
            (1,56,(0x54,(0x1954,10))), # wrong holder info register
            (1,67,(0x0c,(0x070c,))), # result != stored reference
            (2,33,(0x76,(0x0f76,2,3))), # wrong argument start
        ):
            v=deepcopy(scripts)
            v[section]=[(p,*(replacement if p==pc else (op,w)))
                        for p,op,w in v[section]]
            variants.append(v)
        overwritten=deepcopy(scripts)
        overwritten[2].insert(1,(20,0x07,(0x1307,)))
        variants.append(overwritten)
        for idx,case in enumerate(variants):
            with self.subTest(idx=idx):
                with self.assertRaisesRegex(ValueError,"QUEUE_PERIOD_INFO_"):
                    self._check(case,targets,hf,pf)


class SignedPeriodIdConstructorDiscoveryTests(unittest.TestCase):
    def test_distinct_typed_constructor_references_stay_structural_only(self):
        from exo_queue_slot_role_exact import validate_signed_period_id_ctor_sites
        rows=[
            ("Lsynthetic;","first","()V",12,"(Ljava/lang/Object;IIJI)V",0x70),
            ("Lsynthetic;","second","()V",18,"(Ljava/lang/Object;J)V",0x76),
        ]
        result=validate_signed_period_id_ctor_sites(rows)
        self.assertEqual(result["exact_direct_constructor_callsite_count"],2)
        self.assertFalse(result["selected_player_item_generation_at_audio_read_proven"])

    def test_missing_duplicate_wrong_opcode_signature_and_pc_fail_closed(self):
        from exo_queue_slot_role_exact import validate_signed_period_id_ctor_sites
        good=("Lsynthetic;","first","()V",12,"(Ljava/lang/Object;IIJI)V",0x70)
        bad=[[],[good,good],
             [(*good[:3],-1,*good[4:])],
             [(*good[:4],"(Ljava/lang/Object;IIJI)J",0x70)],
             [(*good[:5],0x6e)]]
        for candidate in bad:
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(ValueError,"QUEUE_PERIOD_ID_CTOR_"):
                    validate_signed_period_id_ctor_sites(candidate)


class SignedPeriodIdPinnedSiteGuardTests(unittest.TestCase):
    def test_all_15_original_direct_sites_pinned_fail_closed(self):
        from exo_queue_slot_role_exact import (
            SIGNED_PERIOD_ID_CTOR_DIRECT_SITES,
            validate_signed_period_id_ctor_sites,
        )
        sites=list(SIGNED_PERIOD_ID_CTOR_DIRECT_SITES)
        self.assertEqual(len(sites),15)
        self.assertEqual(validate_signed_period_id_ctor_sites(
            sites,exact_signed=True)["exact_direct_constructor_callsite_count"],15)
        for candidate in (sites[:-1],sites+[
            ("Lfake;","extra","()V",42,"(JLjava/lang/Object;)V",0x70)],
            [(*sites[0][:3],sites[0][3]+1,*sites[0][4:])]+sites[1:]):
            with self.subTest(candidate_len=len(candidate)):
                with self.assertRaisesRegex(ValueError,"QUEUE_PERIOD_ID_CTOR_"):
                    validate_signed_period_id_ctor_sites(candidate,exact_signed=True)


class SignedQueueWideRegisterShapeTests(unittest.TestCase):
    def test_move_wide_register_decoding_and_no_literal_values(self):
        from exo_queue_slot_role_exact import wide_definition_register_shape as shape
        self.assertEqual(shape(4,0x04,(0x3204,)),
                         {"pc":4,"kind":"MOVE_WIDE","dest":2,"source":3})
        self.assertEqual(shape(5,0x05,(0x0905,16)),
                         {"pc":5,"kind":"MOVE_WIDE_FROM16","dest":9,"source":16})
        self.assertEqual(shape(6,0x06,(0x0006,18,21)),
                         {"pc":6,"kind":"MOVE_WIDE_16","dest":18,"source":21})
        self.assertEqual(shape(7,0x53,(0x2153,999)),
                         {"pc":7,"kind":"IGET_WIDE","dest":1})
        self.assertEqual(shape(8,0x16,(0x0416,1234)),
                         {"pc":8,"kind":"CONST_WIDE_16","dest":4})
        self.assertIsNone(shape(9,0x70,(0x0070,10,0)))


class SignedIdLongOriginalQueueCfgTests(unittest.TestCase):
    def _cfg_fixture(self,skipped=False,clobber=False):
        from exo_queue_slot_role_exact import QUEUE, PERIOD_ID
        class Dex:
            def method(self,index): return (PERIOD_ID,"<init>","(JLjava/lang/Object;)V")
        dex=Dex()
        ins={
          0:(0x05,(0x0305,6)),
          2:(0x05,(0x0105,6)),
          4:(0x05,(0x0205,6)),
          6:(0x70,(0x0070,1,0x0321)),
        }
        if clobber: ins[2]=(0x16,(0x0616,0))
        if skipped:
            ins[0]=(0x32,(0x1032,6))
        successors={0:[2,6] if skipped else [2],2:[4],4:[6],6:[]}
        cfg={"by_pc":ins,"successors":successors,
             "entry":0,"reachable":{0,2,4,6}}
        return dex,cfg
    def test_dominator_blocks_shortcut_and_wide_clobber(self):
        from exo_queue_slot_role_exact import verify_signed_id_long_normal_cfg,QUEUE,audit
        from unittest.mock import patch
        method=(QUEUE,"fixture","(J)V")
        for skipped,clobber in ((False,False),(True,False),(False,True)):
            dex,cfg=self._cfg_fixture(skipped,clobber)
            with patch.object(audit,"build_dex_control_flow",return_value=cfg), \
                 patch.object(audit,"typed_parameter_registers",return_value={6}), \
                 patch.object(audit,"invoke_registers",return_value=[1,2,3,4]), \
                 patch.object(audit,"parse_types",return_value=["J","Ljava/lang/Object;"]):
                # The synthetic invoke carries long in v2; move v2 <- p6.
                result=verify_signed_id_long_normal_cfg(
                    dex,method,0,0,6,4,6,2)
            if skipped or clobber:
                self.assertFalse(result["original_caller_J_parameter_proven_at_ctor_on_normal_paths"])
            else:
                self.assertTrue(result["original_caller_J_parameter_proven_at_ctor_on_normal_paths"])


class SignedQueueIdBuilderCallerDiscoveryTests(unittest.TestCase):
    def test_reject_duplicate_unexpected_target_and_wrong_opcode(self):
        from exo_queue_slot_role_exact import (
            validate_signed_queue_id_builder_callers, SIGNED_QUEUE_ID_BUILDERS)
        method=("Lsynthetic;","test","()V")
        callee=sorted(SIGNED_QUEUE_ID_BUILDERS)[0]
        row=(*method,5,callee,0x71)
        result=validate_signed_queue_id_builder_callers([row])
        self.assertEqual(result["exact_direct_callsite_count"],1)
        self.assertFalse(result["original_queue_epoch_or_selected_edition_proven"])
        for bad in ([],[row,row],
                    [(*method,5,("Lbad;","test","()V"),0x71)],
                    [(*method,5,callee,0x12)]):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError,"QUEUE_ID_BUILDERS_"):
                    validate_signed_queue_id_builder_callers(bad)


class SignedQueueIdBuilderPinnedSitesTests(unittest.TestCase):
    def test_exact_eight_caller_sites_negative_mutations(self):
        from exo_queue_slot_role_exact import (
            SIGNED_QUEUE_ID_BUILDER_PINNED_DIRECT_SITES,
            validate_signed_queue_id_builder_callers)
        baseline=list(SIGNED_QUEUE_ID_BUILDER_PINNED_DIRECT_SITES)
        self.assertEqual(validate_signed_queue_id_builder_callers(
            baseline,exact_signed=True)["exact_direct_callsite_count"],8)
        for alternate in (
            baseline[:-1],
            baseline+[baseline[0]],
            [(*baseline[0][:3],baseline[0][3]+1,*baseline[0][4:])]+baseline[1:],
            baseline+[("Lsynthetic;","bad","()V",9,baseline[0][4],0x71)],
        ):
            with self.subTest(count=len(alternate)):
                with self.assertRaisesRegex(ValueError,"QUEUE_ID_BUILDERS_"):
                    validate_signed_queue_id_builder_callers(alternate,exact_signed=True)


class SignedWideFieldOwnerOnlyTests(unittest.TestCase):
    def test_typed_iget_wide_shape_no_field_name_or_value(self):
        from exo_queue_slot_role_exact import signed_wide_writer_type_only as typed,audit
        from unittest.mock import patch
        dex=object()
        with patch.object(audit,"field_id",return_value=("Lsynthetic;","PRIVATE_SECRET","J")):
            row=typed(dex,5,0x53,(0x2153,10))
        self.assertEqual(row["declaring_class"],"Lsynthetic;")
        self.assertEqual(row["instance_field_receiver_register"],2)
        self.assertEqual(row["dest"],1)
        self.assertNotIn("PRIVATE_SECRET",str(row))
        with patch.object(audit,"field_id",return_value=("Lsynthetic;","private","I")):
            with self.assertRaisesRegex(ValueError,"QUEUE_WIDE_OWNER_FIELD_TYPE_MISMATCH"):
                typed(dex,5,0x53,(0x2153,10))


class SignedOldPeriodIdJReuseCfgTests(unittest.TestCase):
    def _scenario(self,skipped=False,clobbered=False):
        from exo_queue_slot_role_exact import (
            QUEUE,PERIOD_ID,SIGNED_OLD_ID_J_REUSE_CALLER,
            SIGNED_OLD_ID_J_REUSE_SITES)
        class Dex:
            def method(self,index):
                return SIGNED_OLD_ID_J_REUSE_SITES[0][2] if index==1 else SIGNED_OLD_ID_J_REUSE_SITES[1][2]
        dex=Dex()
        id_dex=object()
        make=lambda op,receiver,value:((receiver<<12)|(value<<8)|op)
        src13=(0x53,(make(0x53,9,8),10))
        src30=(0x53,(make(0x53,9,7),10))
        ins={0:(0x12,(0x0012,)),13:src13,
             24:(0x12,(0x0012,)),
             25:(0x74,(0x0074,1,0)),
             30:src30,40:(0x74,(0x0074,2,0))}
        if clobbered:ins[24]=(0x16,(0x0816,0))
        successors={0:[13,25] if skipped else [13],13:[24],24:[25],
                    25:[30],30:[40],40:[]}
        cfg={"by_pc":ins,"successors":successors,
             "entry":0,"reachable":set(ins)}
        targets={
            SIGNED_OLD_ID_J_REUSE_CALLER:(dex,0,1),
            (PERIOD_ID,"<init>","(Ljava/lang/Object;IIJI)V"):(id_dex,0,2)
        }
        return dex,id_dex,targets,cfg
    def test_exact_id_field_reuse_is_not_automatically_selected_epoch(self):
        from exo_queue_slot_role_exact import (
            verify_signed_old_period_id_long_handoff,audit,PERIOD_ID)
        from unittest.mock import patch
        for skipped,clobbered in ((False,False),(True,False),(False,True)):
            dex,id_dex,targets,cfg=self._scenario(skipped,clobbered)
            insn_ctor=[(9,0x5a,(0x005a,10))]
            with patch.object(audit,"instructions",side_effect=lambda _dex,off: insn_ctor if off==2 else []), \
                 patch.object(audit,"field_id",return_value=(PERIOD_ID,"private","J")), \
                 patch.object(audit,"build_dex_control_flow",return_value=cfg), \
                 patch.object(audit,"typed_parameter_registers",return_value={9}), \
                 patch.object(audit,"invoke_registers",side_effect=lambda op,words:
                     [0,0,0,0,0,6,0,8,0,0] if words[1]==1 else
                     [0,0,0,3,0,5,0,7,0,0]), \
                 patch.object(audit,"parse_types",side_effect=lambda sig:
                     ["LTva;","Ljava/lang/Object;","I","I","J","J","Z"] if "IIJJZ" in sig else
                     ["LTva;","Ljava/lang/Object;","J","J","J","Z"]):
                witness=verify_signed_old_period_id_long_handoff(targets)
            if skipped or clobbered:
                self.assertFalse(witness["old_id_J_field_reaches_two_builder_paths_on_all_normal_cfg"])
            else:
                self.assertTrue(witness["old_id_J_field_reaches_two_builder_paths_on_all_normal_cfg"])
            self.assertFalse(witness["current_selected_item_or_unique_playback_generation_proven"])

if __name__=="__main__": unittest.main()

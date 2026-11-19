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
        src13=(0x53,(make(0x53,13,8),10))
        src30=(0x53,(make(0x53,13,7),10))
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
                 patch.object(audit,"typed_parameter_registers",return_value={13}), \
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


class SignedSelectedTimelineCandidateWindowTests(unittest.TestCase):
    def test_scout_exact_scoped_field_type_only_and_false_selection(self):
        from exo_queue_slot_role_exact import signed_selector_window,PLAYBACK_INFO
        from exo_queue_slot_role_exact import audit
        from unittest.mock import patch
        class FakeDex:
            def method(self,idx):return ("Lunrelated;","other","()V")
        fake=FakeDex()
        ins=[
            (3,0x54,(0x1254,8)),
            (5,0x54,(0x0354,9)),
            (7,0x32,(0x0032,2)),
            (10,0x11,(0x0211,))
        ]
        with patch.object(audit,"instructions",return_value=ins), \
             patch.object(audit,"field_id",side_effect=lambda dex,index:
                 (PLAYBACK_INFO,"DO_NOT_LEAK","LTva;") if index==8
                 else ("Lunrelated;","SECRET","I")):
            view=signed_selector_window(fake,("Ltest;","test","()V"),0,100,((0,10),))
        self.assertFalse(view["runtime_current_selected_item_or_period_proven"])
        self.assertEqual([x["pc"] for x in view["scoped_type_reference_rows"]],[3,7,10])
        self.assertNotIn("DO_NOT_LEAK",str(view))
        self.assertNotIn("SECRET",str(view))


class SignedSelectedStateFieldCorrespondenceTests(unittest.TestCase):
    def test_field_correspondence_names_never_exported(self):
        from exo_queue_slot_role_exact import (
            signed_selected_state_field_correspondence,
            PLAYER_STATE_RESOLVE,ENGINE,HOLDER,PERIOD_INFO)
        from exo_queue_slot_role_exact import audit
        from unittest.mock import patch
        hctor=(HOLDER,"<init>","([Landroidx/media3/exoplayer/l;JLOFa;LrH2;Landroidx/media3/exoplayer/i;Lyh6;LRFa;)V")
        ctor=(PERIOD_INFO,"<init>","(LSl6$b;JJJJZZZZZ)V")
        class FakeDex:
            pass
        sources={ENGINE:{671:(0x54,(0x0054,1)),1260:(0x54,(0x0054,1)),
                  673:(0x54,(0x0054,2)),1262:(0x54,(0x0054,3)),
                  675:(0x54,(0x0054,4)),679:(0x54,(0x0054,4)),
                  677:(0x54,(0x0054,5)),681:(0x54,(0x0054,5))},
                 PLAYER_STATE_RESOLVE:{
                    25:(0x54,(0x0054,2)),
                    74:(0x54,(0x0054,7)),96:(0x54,(0x0054,7)),
                    138:(0x54,(0x0054,8)),257:(0x54,(0x0054,3)),
                    259:(0x54,(0x0054,8))},
                 hctor:{18:(0x5b,(0x005b,4))},
                 ctor:{48:(0x5b,(0x005b,5))}}
        fields={
            1:(ENGINE[0],"SECRET_PLAYBACK","LCD7;"),
            2:("LCD7;","PRIVATE_TIMELINE","LTva;"),
            3:("LCD7;","PRIVATE_CURRENT","LSl6$b;"),
            4:(HOLDER,"PRIVATE_INFO",PERIOD_INFO),
            5:(PERIOD_INFO,"PRIVATE_ID","LSl6$b;"),
            7:("LCD7;","PRIVATE_LOADING","LSl6$b;"),
            8:("LCD7;","PRIVATE_SECONDARY","LSl6$b;")}
        targets={}
        lookup={}
        for ix,m in enumerate(sources):
            dex=FakeDex()
            targets[m]=(dex,0,ix)
            lookup[ix]=[(pc,op,w) for pc,(op,w) in sources[m].items()]
        with patch.object(audit,"instructions",side_effect=lambda dex,offset: lookup[offset]), \
             patch.object(audit,"field_id",side_effect=lambda dex,index:fields[index]):
            view=signed_selected_state_field_correspondence(targets)
        self.assertTrue(view["engine_timeline_field_matches_player_M0"])
        self.assertTrue(view["engine_playback_info_two_reads_same_exact_field"])
        self.assertEqual(view["engine_player_ID_field_exact_M0_iget_match_PCs"],[257])
        self.assertFalse(view["runtime_simultaneous_snapshot_proven"])
        self.assertNotIn("SECRET",str(view))
        self.assertNotIn("PRIVATE",str(view))


class SignedPlayerFrontUIDEqualsTests(unittest.TestCase):
    def _fixture(self,alter=None):
        from exo_queue_slot_role_exact import (
            ENGINE,PLAYER_STATE_RESOLVE,ENGINE_PLAYER_FRONT,
            HOLDER,PERIOD_INFO,PLAYBACK_INFO,PERIOD_ID)
        class Dex:
            def method(self,index):
                return {1:ENGINE_PLAYER_FRONT,2:("Ljava/lang/Object;","getClass","()Ljava/lang/Class;"),
                        3:("Ljava/lang/Object;","equals","(Ljava/lang/Object;)Z")}[index]
        engine=Dex();player=Dex()
        def w(op,dst,receiver,field):
            return ((receiver<<12)|(dst<<8)|op,field)
        instructions={
            671:(0x54,w(0x54,5,0,1)),675:(0x54,w(0x54,6,3,4)),677:(0x54,w(0x54,6,6,5)),
            1253:(0x6e,(0x016e,1,0x000a)),
            1256:(0x0c,(0x0b0c,)),
            1257:(0x6e,(0x016e,2,0x000b)),
            1260:(0x54,w(0x54,1,0,1)),
            1262:(0x54,w(0x54,1,1,3)),
            1264:(0x54,w(0x54,1,1,7)),
            1266:(0x54,w(0x54,2,11,4)),
            1268:(0x54,w(0x54,2,2,5)),
            1270:(0x54,w(0x54,2,2,7)),
            1272:(0x6e,(0x026e,3,0x0021)),
            1275:(0x0a,(0x010a,)),
            1276:(0x38,(0x0138,27)),
        }
        if alter:
            pc,opcode,words=alter
            instructions[pc]=(opcode,words)
        fields={1:(ENGINE[0],"engineInfo",PLAYBACK_INFO),
                3:(PLAYBACK_INFO,"playingId",PERIOD_ID),
                4:(HOLDER,"periodInfo",PERIOD_INFO),
                5:(PERIOD_INFO,"id",PERIOD_ID),
                7:(PERIOD_ID,"uid","Ljava/lang/Object;"),
                8:(PERIOD_ID,"differentUid","Ljava/lang/Object;")}
        targets={ENGINE:(engine,0,100),PLAYER_STATE_RESOLVE:(player,0,200),
                 ENGINE_PLAYER_FRONT:(object(),0,300)}
        source_by_offset={100:[(pc,op,w) for pc,(op,w) in instructions.items()],
                          200:[(74,0x54,w(0x54,1,1,3))]}
        return targets,fields,source_by_offset
    def _prove(self,alter=None):
        from exo_queue_slot_role_exact import (
            verify_signed_player_info_front_UID_comparison,audit)
        from unittest.mock import patch
        targets,fields,sources=self._fixture(alter)
        with patch.object(audit,"instructions",side_effect=lambda dex,off:sources[off]), \
             patch.object(audit,"field_id",side_effect=lambda dex,index:fields[index]), \
             patch.object(audit,"invoke_registers",side_effect=lambda opcode,w:
                 {1:[10],2:[11],3:[1,2]}[w[1]]):
            return verify_signed_player_info_front_UID_comparison(targets)
    def test_proven_comparison_is_not_runtime_equals_or_selected_item(self):
        result=self._prove()
        self.assertTrue(result["original_java_equals_receives_player_uid_and_front_holder_uid"])
        self.assertFalse(result["started_audio_read_same_snapshot_proven"])
        self.assertFalse(result["selected_track_edition_or_unique_generation_proven"])
    def test_wrong_uid_field_equals_target_and_front_holder_fail_closed(self):
        changes=[
            (1270,0x54,(0x2254,8)),
            (1276,0x38,(0x0138,26)),
            (1256,0x0c,(0x0a0c,)),
            (1272,0x6e,(0x026e,2,0x0021)),
        ]
        for case in changes:
            with self.subTest(case=case):
                with self.assertRaisesRegex(ValueError,"PLAYER_FRONT_IDENTITY_"):
                    self._prove(case)


class SignedEnginePeriodTimelineTransitionTests(unittest.TestCase):
    def test_exact_callsite_rejects_missing_and_wrong_target(self):
        from exo_queue_slot_role_exact import (
            inspect_signed_engine_period_timeline_transition,
            ENGINE,ENGINE_PERIOD_TIMELINE_TRANSITION,audit)
        from unittest.mock import patch
        class FakeDex:
            def __init__(self,target):self.target=target
            def method(self,index):return self.target
        bad={"missing":False,"wrong":True}
        for variant in bad:
            rows=[
                (673,0x54,(0x0554,1)),(677,0x54,(0x0654,2)),
                (681,0x54,(0x0154,3)),(686,0x07,(0x0207,)),
                (687,0x07,(0x0407,)),(688,0x07,(0x0107,)),
                (699,0x07,(0x0307,)),(711,0x76,(0x0876,5,0)),
            ]
            if variant=="missing":rows=[x for x in rows if x[0]!=711]
            engine=FakeDex(("Lbogus;","notIt","()V") if variant=="wrong"
                           else ENGINE_PERIOD_TIMELINE_TRANSITION)
            transition=FakeDex(None)
            targets={ENGINE:(engine,0,1),
                     ENGINE_PERIOD_TIMELINE_TRANSITION:(transition,0,2)}
            with patch.object(audit,"instructions",side_effect=lambda d,off:rows if off==1 else []), \
                 patch.object(audit,"invoke_registers",return_value=[0]*8):
                with self.subTest(variant=variant):
                    with self.assertRaisesRegex(ValueError,"PERIOD_TIMELINE_"):
                        inspect_signed_engine_period_timeline_transition(targets)


class SignedTwoSlotBTransitionFailClosedTests(unittest.TestCase):
    def test_reject_wrong_old_new_slot_or_method(self):
        from exo_queue_slot_role_exact import (
            signed_two_slotB_reads_to_timeline_transition,QUEUE,HOLDER,PERIOD_INFO,PERIOD_ID,
            PLAYBACK_INFO,TIMELINE,ENGINE,ENGINE_PERIOD_TIMELINE_TRANSITION,audit)
        from unittest.mock import patch
        class Dex:
            def method(self,index):return ENGINE_PERIOD_TIMELINE_TRANSITION
        dex=Dex()
        def w(op,dst,recv,index):
            return ((recv<<12)|(dst<<8)|op,index)
        rows={
          547:(0x54,w(0x54,1,9,1)),
          659:(0x5b,w(0x5b,3,9,1)),
          664:(0x54,w(0x54,3,9,1)),
          673:(0x54,w(0x54,5,5,4)),
          675:(0x54,w(0x54,6,3,2)),
          677:(0x54,w(0x54,6,6,3)),
          679:(0x54,w(0x54,1,1,2)),
          681:(0x54,w(0x54,1,1,3)),
          686:(0x07,(0x6207,)),
          687:(0x07,(0x1407,)),
          688:(0x07,(0x5107,)),
          699:(0x07,(0x1307,)),
          711:(0x76,(0x0876,5,0)),
        }
        fields={1:(QUEUE,"b",HOLDER),2:(HOLDER,"info",PERIOD_INFO),
                3:(PERIOD_INFO,"id",PERIOD_ID),4:(PLAYBACK_INFO,"timeline",TIMELINE),
                5:(QUEUE,"wrong",HOLDER)}
        targets={ENGINE:(dex,0,1)}
        with patch.object(audit,"instructions",side_effect=lambda d,off:
                 [(pc,op,words) for pc,(op,words) in rows.items()]), \
             patch.object(audit,"field_id",side_effect=lambda d,i:fields[i]), \
             patch.object(audit,"invoke_registers",return_value=[0,1,2,3,4,5,6,7]), \
             patch.object(audit,"move_object_registers",side_effect=lambda op,w:
                 ((w[0]>>8)&15,(w[0]>>12)&15)):
            witness=signed_two_slotB_reads_to_timeline_transition(
                targets,{fields[1]:"SLOT_B"})
        self.assertEqual(witness["exact_same_slotB_read_at_pcs"],[547,664])
        self.assertFalse(witness["current_selected_audio_track_edition_or_epoch_proven"])


class SignedTimelinePeriodUIDLookupTests(unittest.TestCase):
    def _prove(self,uid_drift=False,callee_drift=False):
        from exo_queue_slot_role_exact import (
            verify_signed_period_ID_UID_to_timeline_lookup,
            ENGINE,ENGINE_PERIOD_TIMELINE_TRANSITION,ENGINE_PERIOD_STATUS_PREDICATE,
            EXACT_TIMELINE_PERIOD_BY_UID,PERIOD_ID,TIMELINE,audit)
        from unittest.mock import patch
        class FakeDex:
            def method(self,index):
                return ("Lfake;","bad","()V") if callee_drift else EXACT_TIMELINE_PERIOD_BY_UID
        positions={ENGINE:1,ENGINE_PERIOD_TIMELINE_TRANSITION:2,ENGINE_PERIOD_STATUS_PREDICATE:3}
        data={
            1:[(1264,0x54,(0x1154,7))],
            2:[(52,0x54,(0x8854,7 if not uid_drift else 8)),
               (56,0x6e,(0x036e,1,0x0870)),
               (99,0x54,(0xa854,7)),
               (101,0x6e,(0x036e,1,0x0890))],
            3:[(13,0x54,(0x4454,7)),
               (17,0x6e,(0x036e,1,0x0430))]
        }
        targets={k:(FakeDex(),0,pos) for k,pos in positions.items()}
        def invoke(op,words):
            return {0x0870:[7,8,0],0x0890:[9,8,0],0x0430:[3,4,0]}[words[2]]
        def params(dex,method,flags,off,typ):
            if off==2:return {8,10} if typ==PERIOD_ID else {7,9}
            return {4} if typ==PERIOD_ID else {3}
        with patch.object(audit,"instructions",side_effect=lambda dex,off:data[off]), \
             patch.object(audit,"field_id",side_effect=lambda dex,index:
                (PERIOD_ID,"sameUID","Ljava/lang/Object;") if index==7
                 else (PERIOD_ID,"OTHER_UID","Ljava/lang/Object;")), \
             patch.object(audit,"invoke_registers",side_effect=invoke), \
             patch.object(audit,"typed_parameter_registers",side_effect=params):
            return verify_signed_period_ID_UID_to_timeline_lookup(targets)
    def test_same_exact_original_period_UID_field_not_selection_proof(self):
        v=self._prove()
        self.assertTrue(v["three_exact_signed_ID_UID_to_timeline_period_lookups"])
        self.assertFalse(v["NAV41_readonly_runtime_admission_proven"])
    def test_changed_UID_field_or_lookup_callee_fail_closed(self):
        for uid_drift,callee_drift in ((True,False),(False,True)):
            with self.subTest(uid_drift=uid_drift,callee_drift=callee_drift):
                with self.assertRaisesRegex(ValueError,"TIMELINE_UID_"):
                    self._prove(uid_drift,callee_drift)



class SignedFrontPostUIDSentinelGuardTests(unittest.TestCase):
    def _verify(self,change=None):
        from exo_queue_slot_role_exact import (
            verify_signed_player_front_post_UID_guard,ENGINE,HOLDER,
            PLAYBACK_INFO,PERIOD_INFO,PERIOD_ID,audit)
        from unittest.mock import patch
        class Dex:pass
        dex=Dex()
        def f(op,dest,recv,idx):
            return (op|(dest<<8)|(recv<<12),idx)
        def b(op,a,c,pc):
            return (op|(a<<8)|(c<<12),1303-pc)
        rows={
            1260:(0x54,f(0x54,1,0,1)),1262:(0x54,f(0x54,1,1,2)),
            1266:(0x54,f(0x54,2,11,3)),1268:(0x54,f(0x54,2,2,4)),
            1278:(0x54,f(0x54,1,0,1)),1280:(0x54,f(0x54,1,1,2)),
            1282:(0x52,f(0x52,2,1,5)),1284:(0x12,(0xf312,)),
            1285:(0x33,b(0x33,2,3,1285)),
            1287:(0x54,f(0x54,2,11,3)),1289:(0x54,f(0x54,2,2,4)),
            1291:(0x52,f(0x52,4,2,5)),
            1293:(0x33,b(0x33,4,3,1293)),
            1295:(0x52,f(0x52,1,1,6)),1297:(0x52,f(0x52,2,2,6)),
            1299:(0x32,b(0x32,1,2,1299))}
        if change:
            pc,entry=change
            rows[pc]=entry
        fields={1:(ENGINE[0],"SECRET_INFO",PLAYBACK_INFO),
                2:(PLAYBACK_INFO,"SECRET_ID",PERIOD_ID),
                3:(HOLDER,"SECRET_HOLDER",PERIOD_INFO),
                4:(PERIOD_INFO,"SECRET_PERIOD_ID",PERIOD_ID),
                5:(PERIOD_ID,"SECRET_FIRST_INT","I"),
                6:(PERIOD_ID,"SECRET_SECOND_INT","I"),
                7:(PERIOD_ID,"DRIFT","I")}
        targets={ENGINE:(dex,0,1)}
        with patch.object(audit,"instructions",return_value=[
            (pc,op,w) for pc,(op,w) in sorted(rows.items())]), \
             patch.object(audit,"field_id",side_effect=lambda d,idx:fields[idx]):
            return verify_signed_player_front_post_UID_guard(targets)
    def test_all_three_original_post_uid_comparisons_do_not_prove_audible_selection(self):
        v=self._verify()
        self.assertTrue(v["post_UID_both_IDs_test_same_exact_first_int_field_against_minus_one"])
        self.assertTrue(v["second_int_field_same_for_both_and_distinct_from_first"])
        self.assertFalse(v["selected_media_item_or_edition_proven"])
        self.assertNotIn("SECRET",str(v))
    def test_wrong_field_literal_branch_opcode_register_and_target_fail_closed(self):
        changes=[
            (1291,(0x52,(0x2452,7))),
            (1284,(0x12,(0x0312,))),
            (1299,(0x33,(0x2133,4))),
            (1293,(0x33,(0x2333,10))),
            (1280,(0x54,(0x1154,7))),
            (1285,(0x33,(0x2333,17))),
        ]
        for case in changes:
            with self.subTest(case=case):
                with self.assertRaisesRegex(ValueError,"FRONT_POST_UID_"):
                    self._verify(case)


class SignedTimelinePeriodWindowScopedSurveyTests(unittest.TestCase):
    def test_keeps_private_fields_hidden_and_selection_unproved(self):
        from exo_queue_slot_role_exact import (
            signed_period_window_bounded_scout,ENGINE_PERIOD_TIMELINE_TRANSITION,
            ENGINE_PERIOD_STATUS_PREDICATE,TIMELINE_PERIOD,TIMELINE_WINDOW,
            TIMELINE,audit)
        from unittest.mock import patch
        class FakeDex:
            def method(self,i):return (TIMELINE,"super","(ILTva$d;)V")
        dex=FakeDex()
        targets={
            ENGINE_PERIOD_TIMELINE_TRANSITION:(dex,0,1),
            ENGINE_PERIOD_STATUS_PREDICATE:(dex,0,2)}
        instructions=[(3,0x54,(0x1254,10)),(7,0x6e,(0x006e,0,0)),
                      (9,0x0c,(0x010c,))]
        with patch.object(audit,"instructions",return_value=instructions), \
             patch.object(audit,"field_id",return_value=(TIMELINE_PERIOD,"DO_NOT_LOG","I")), \
             patch.object(audit,"invoke_registers",return_value=[7,1,2]):
            view=signed_period_window_bounded_scout(targets)
        self.assertFalse(view["period_to_window_current_selection_proven"])
        self.assertNotIn("DO_NOT_LOG",str(view))
        self.assertEqual(view["scoped_signed_methods"]["I"]["rows"][0]["type"],"I")



class SignedPeriodRecordToWindowExactTests(unittest.TestCase):
    def _run(self,mutation=None):
        from exo_queue_slot_role_exact import (
            verify_signed_period_record_window_handoffs,ENGINE,
            ENGINE_PERIOD_TIMELINE_TRANSITION,ENGINE_PERIOD_STATUS_PREDICATE,
            TIMELINE_PERIOD,TIMELINE_WINDOW,TIMELINE,
            EXACT_TIMELINE_PERIOD_BY_UID,EXACT_TIMELINE_WINDOW_BY_INDEX,
            EXACT_TIMELINE_WINDOW_AT_POSITION,audit)
        from unittest.mock import patch
        class Dex:
            def method(self,i):
                return {1:EXACT_TIMELINE_PERIOD_BY_UID,
                        2:EXACT_TIMELINE_WINDOW_BY_INDEX,
                        3:EXACT_TIMELINE_WINDOW_AT_POSITION}[i]
        dex=Dex()
        def field(op,dst,recv,i):return (op|(dst<<8)|(recv<<12),i)
        def call(i):return (0x006e,i,0)
        def result(reg):return (0x0c|(reg<<8),)
        first={
            54:(0x54,field(0x54,0,6,1)),
            56:(0x6e,call(1)),59:(0x0c,result(1)),
            60:(0x52,field(0x52,1,1,3)),
            62:(0x54,field(0x54,2,6,2)),
            64:(0x6e,call(2)),67:(0x54,field(0x54,1,2,4)),
            101:(0x6e,call(1)),104:(0x0c,result(8)),
            105:(0x52,field(0x52,8,8,3)),
            109:(0x6e,call(3)),112:(0x0c,result(8)),
            113:(0x54,field(0x54,8,8,5))}
        second={
            15:(0x54,field(0x54,0,2,1)),
            17:(0x6e,call(1)),20:(0x0c,result(4)),
            21:(0x52,field(0x52,4,4,3)),
            23:(0x54,field(0x54,0,2,2)),
            25:(0x6e,call(2))}
        if mutation:
            site,pc,row=mutation
            (first if site=="I" else second)[pc]=row
        fields={1:(ENGINE[0],"SECRET_PERIOD",TIMELINE_PERIOD),
                2:(ENGINE[0],"SECRET_WINDOW",TIMELINE_WINDOW),
                3:(TIMELINE_PERIOD,"SECRET_INT","I"),
                4:(TIMELINE_WINDOW,"PRIVATE_ITEM_CONFIG","LOf6$f;"),
                5:(TIMELINE_WINDOW,"PRIVATE_OBJECT","Ljava/lang/Object;"),
                6:(TIMELINE_PERIOD,"DIFFERENT_INT","I"),
                7:(ENGINE[0],"DIFFERENT_WINDOW",TIMELINE_WINDOW)}
        targets={ENGINE_PERIOD_TIMELINE_TRANSITION:(dex,0,1),
                 ENGINE_PERIOD_STATUS_PREDICATE:(dex,0,2)}
        regsets={("I",56):[7,8,0],("I",64):[7,1,2],
                 ("I",101):[9,8,0],("I",109):[9,8,2,10,11],
                 ("z",17):[3,4,0],("z",25):[3,4,0]}
        at=iter(())
        def inv(op,w):
            ident=w[1]
            for method,insns in (("I",first),("z",second)):
                for pc,(code,words) in insns.items():
                    if code in audit.INVOKES and words is w:
                        return regsets[(method,pc)]
            raise AssertionError("unmapped fixture invoke")
        with patch.object(audit,"instructions",side_effect=lambda d,off:[
            (pc,op,w) for pc,(op,w) in sorted((first if off==1 else second).items())]), \
             patch.object(audit,"field_id",side_effect=lambda d,i:fields[i]), \
             patch.object(audit,"invoke_registers",side_effect=inv):
            return verify_signed_period_record_window_handoffs(targets)
    def test_exact_three_signed_uid_to_period_to_window_paths_without_selected_claim(self):
        value=self._run()
        self.assertTrue(value["three_original_period_records_expose_same_exact_int_field"])
        self.assertFalse(value["NAV41_readonly_runtime_admission_proven"])
        self.assertNotIn("SECRET",str(value))
        self.assertNotIn("PRIVATE",str(value))
    def test_reject_wrong_period_field_window_field_invocation_and_register(self):
        def f(op,d,r,i):return (op|(d<<8)|(r<<12),i)
        cases=[
            ("I",105,(0x52,f(0x52,8,8,6))),
            ("z",23,(0x54,f(0x54,0,2,7))),
            ("I",109,(0x6e,(0x006e,2,0))),
            ("I",59,(0x0c,(0x020c,))),
            ("z",21,(0x52,f(0x52,5,4,3))),
            ("I",67,(0x54,f(0x54,1,1,4))),
            ("I",61,(0x01,(0x1101,))),
        ]
        for changed in cases:
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(ValueError,"PERIOD_WINDOW_"):
                    self._run(changed)



class SignedWindowGetCurrentItemFieldDistinctionTests(unittest.TestCase):
    def _run(self,change=None,without_getter=False):
        from exo_queue_slot_role_exact import (
            verify_signed_window_field_is_not_current_mediaitem,
            PLAYER_CURRENT_MEDIAITEM_GETTER,ENGINE_PERIOD_TIMELINE_TRANSITION,
            TIMELINE_WINDOW,audit)
        from unittest.mock import patch
        class Dex:pass
        d1=Dex();d2=Dex()
        getter=[(5,0x54,(0x1054,1))]
        engine=[(67,0x54,(0x2154,2))]
        if change:
            which,row=change
            (getter if which=="getter" else engine)[0]=row
        targets={ENGINE_PERIOD_TIMELINE_TRANSITION:(d2,0,2)}
        if not without_getter:targets[PLAYER_CURRENT_MEDIAITEM_GETTER]=(d1,0,1)
        def field(d,i):
            if d is d1:
                return (TIMELINE_WINDOW,"SECRET_MEDIA_ITEM","LOf6;" if i==1 else "LOf6$f;")
            return (TIMELINE_WINDOW,"SECRET_LIVE_CONFIG","LOf6$f;" if i==2 else "LOf6;")
        with patch.object(audit,"instructions",side_effect=lambda d,off:getter if off==1 else engine), \
             patch.object(audit,"field_id",side_effect=field):
            return verify_signed_window_field_is_not_current_mediaitem(targets)
    def test_distinct_window_field_is_not_active_mediaitem_proof(self):
        r=self._run()
        self.assertTrue(r["the_two_exact_original_window_field_references_distinct"])
        self.assertFalse(r["same_original_window_instance_between_getter_and_e_I_proven"])
        self.assertNotIn("SECRET",str(r))
    def test_missing_getter_wrong_type_and_wrong_register_fail_closed(self):
        checks=[
            (("getter",(5,0x54,(0x1054,3))),False),
            (("engine",(67,0x54,(0x2154,3))),False),
            (("engine",(67,0x54,(0x3154,2))),False),
            (None,True),
        ]
        for change,without in checks:
            with self.subTest(change=change,without=without):
                with self.assertRaisesRegex(ValueError,"WINDOW_ITEM_FIELD_"):
                    self._run(change,without)



class PublisherNewSDKSignerGateCompatTests(unittest.TestCase):
    def test_old_and_new_output_issuer_gate_strictly_equivalent(self):
        from publisher_2025_provenance_gate import (
            verify_metadata,KNOWN_ISSUER_CERT,VERSION_CODE,VERSION_NAME_GPR,GateError)
        manifest="package: name='ru.yandex.music' versionCode='{}' versionName='{}'".format(
            VERSION_CODE,VERSION_NAME_GPR)
        scheme="Verified using v2 scheme (APK Signature Scheme v2): true\n"
        old="Signer #1 certificate SHA-256 digest: {}\n".format(KNOWN_ISSUER_CERT)+scheme
        modern=("Number of signers: 1\n"
                "V3.0 Signer: certificate SHA-256 digest: {}\n"
                "Source Stamp Signer: certificate SHA-256 digest: {}\n").format(
                    KNOWN_ISSUER_CERT,"0"*64)+scheme
        for output in (old,modern):
            with self.subTest(style=output[:12]):
                self.assertTrue(verify_metadata(manifest,output,expected_version=VERSION_NAME_GPR)[
                    "publisher_cert_matches_verified_rustore_2026_reference"])
        cases=[
            modern.replace("Number of signers: 1","Number of signers: 2"),
            modern.replace("V3.0 Signer: certificate SHA-256 digest: {}".format(KNOWN_ISSUER_CERT),
                           "V3.0 Signer: certificate SHA-256 digest: {}".format("0"*64)),
            modern.replace("V3.0 Signer: certificate SHA-256 digest: {}".format(KNOWN_ISSUER_CERT),""),
            modern.replace("true","false"),
        ]
        for bad in cases:
            with self.subTest(bad=bad[:34]):
                with self.assertRaises(GateError):
                    verify_metadata(manifest,bad,expected_version=VERSION_NAME_GPR)

if __name__=="__main__": unittest.main()

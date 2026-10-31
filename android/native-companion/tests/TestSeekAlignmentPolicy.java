package pro.celikom.nativeprobe.identitydiag;

/** Pure deterministic checks for stable transport-offset capture and seek deltas. */
public final class TestSeekAlignmentPolicy {
 static int checks;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 public static void main(String[] args){
  SeekAlignmentPolicy p=new SeekAlignmentPolicy();
  p.begin(900);
  check(p.withinAcceptance(204)&&!p.withinAcceptance(226),
    "without a stable offset, 204ms is accepted but 226ms requires correction");
  p.reset();
  p.observe(200,1000,true);p.observe(206,1150,true);p.observe(211,1300,true);
  check(p.stableForTest()&&p.stableOffsetForTest()==206,
    "three consistent samples establish median 206ms baseline");
  p.begin(1310);
  check(p.pending()&&p.hasBaseline()&&p.baselineOffset()==206,
    "seek freezes the most recent stable baseline");
  check(p.adjustedDrift(283)==77&&p.withinAcceptance(283),
    "283ms absolute drift is only a 77ms new error over stable 206ms offset");
  check(p.adjustedDrift(226)==20&&p.withinAcceptance(226),
    "226ms raw drift is still accepted when a stable 206ms offset explains it");
  check(p.adjustedDrift(330)==124&&p.withinAcceptance(330),
    "330ms raw drift is acceptable when only 124ms exceeds the stable baseline");
  check(p.adjustedDrift(456)==250&&!p.withinAcceptance(456),
    "456ms raw drift is rejected when it adds 250ms beyond the stable baseline");
  check(p.decoderTarget(50000,120000)==49794,
    "decoder seek preserves the established 206ms source/decoder relationship");
  p.begin(1400);
  check(p.baselineOffset()==206,"repeated scrub does not replace the frozen baseline");
  p.finish(283,1500);
  check(!p.pending()&&p.stableForTest()&&p.stableOffsetForTest()==283
      &&p.supervisedDrift(300)==17,
    "accepted post-seek offset becomes the next steady reference for clock supervision");

  p.reset();
  p.observe(550,2000,true);p.observe(555,2150,true);p.observe(548,2300,true);
  check(p.stableForTest()&&p.stableOffsetForTest()==550,
    "large but stable 550ms route-like offset is retained as transport baseline");
  p.begin(2310);
  check(p.withinAcceptance(600)&&p.adjustedDrift(600)==50,
    "600ms raw drift adds only 50ms to the established 550ms offset");
  p.finish(729,2400);
  check(p.stableForTest()&&p.stableOffsetForTest()==729&&p.supervisedDrift(750)==21,
    "a validated baseline plus an accepted residual may form a derived offset up to 925ms");
  p.reset();p.begin(3000);
  check(!p.hasBaseline()&&p.adjustedDrift(283)==283&&!p.withinAcceptance(283),
    "without stable history the policy fails closed against a 283ms residual");
  p.finish(65,3010);p.begin(3020);
  check(p.hasBaseline()&&p.baselineOffset()==65,
    "a verified small residual seeds the next seek baseline");
  p.reset();
  p.observe(100,4000,true);p.observe(180,4150,true);p.observe(260,4300,true);
  check(!p.stableForTest(),"unstable samples cannot become a baseline");
  p.observe(260,5000,true);
  check(!p.stableForTest(),"a long sample gap restarts stability accumulation");
  p.observe(260,5150,true);p.observe(260,5300,true);
  check(p.stableForTest()&&p.stableOffsetForTest()==260,
    "three new consistent samples re-establish the baseline after a gap");
  p.begin(6600);
  check(!p.hasBaseline(),"stale baseline expires after a long idle gap");
  System.out.println("PASS: "+checks+" seek-scoped transport baseline checks");
 }
}

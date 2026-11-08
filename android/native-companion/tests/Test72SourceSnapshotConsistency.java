package pro.celikom.nativeprobe.identitydiag;

/** Test.71 HONOR replay: Dym -> Rose Wine -> Back to Dym, stale alias 978. */
final class Test72SourceSnapshotConsistency {
 static void expect(boolean valid,String what){if(!valid)throw new AssertionError(what);}
 static SourceSnapshotConsistency.Verdict s(SourceSnapshotConsistency g,String alias,String title,String artist,String cover,long posDuration,long metaDuration){
  return g.observe(alias,title,artist,cover,posDuration,metaDuration);
 }
 public static void main(String[] args){
  SourceSnapshotConsistency g=new SourceSnapshotConsistency();
  expect(s(g,"866","Нас не понимают вообще","Космонавты, RASKOL","album5685525",232330,232330).allowed(),"RASKOL ready");
  expect(s(g,"929","Дым","Лёша Свик","albumDym",219660,219660).allowed(),"Dym BUFFERING is still valid identity");
  expect(s(g,"978","Розовое вино","Элджей, FEDUK","album11530439",246810,246810).allowed(),"Rose Wine READY");
  expect(s(g,"978","Розовое вино","Элджей, FEDUK","album11530439",246810,246810).allowed(),"Rose Wine repeat sample");
  SourceSnapshotConsistency.Verdict broken=s(g,"978","Розовое вино","Элджей, FEDUK","album11530439",219660,246810);
  expect(broken.firstConflict(),"same alias with Dym duration must be flagged");
  expect("unchanged_item_changed_duration".equals(broken.reason),"strong old-item fingerprint");
  expect(!s(g,"978","Розовое вино","Элджей, FEDUK","album11530439",219660,-1).allowed(),"missing metadata extras must not unquarantine");
  expect(!s(g,"978","Розовое вино","Элджей, FEDUK","album11530439",246810,246810).allowed(),"old alias flipping duration back is NOT new song");
  SourceSnapshotConsistency.Verdict dym=s(g,"981","Дым","Лёша Свик","albumDym",219660,219660);
  expect(dym.status==SourceSnapshotConsistency.Status.RECOVERED,"fresh Dym item releases fence");
  expect(s(g,"981","Дым","Лёша Свик","albumDym",219660,219660).allowed(),"steady Dym remains usable");
  expect(s(g,"850","Пушка","10AGE","albumNormal",139000,-1).allowed(),"normal control track without metadata extra");
  expect(s(g,"850","Пушка","10AGE","albumNormal",139700,-1).allowed(),"small duration metadata jitter not a false switch");
  expect(s(g,"851","Нету интереса","10AGE","albumNext",157000,157000).allowed(),"next control track");
  g.clear();
  SourceSnapshotConsistency.Verdict newItem=s(g,"1000","Дым","Лёша Свик","albumDym",246810,219660);
  expect(newItem.status==SourceSnapshotConsistency.Status.CONFLICT,"new alias cross-field mismatch held");
  expect(s(g,"1000","Дым","Лёша Свик","albumDym",219660,219660).status
    ==SourceSnapshotConsistency.Status.RECOVERED,"new alias can settle without invented timeout");
  g.clear();
  expect(s(g,"977","Розовое вино","Элджей, FEDUK","album11530439",246810,-1).allowed(),"baseline without extras");
  expect(s(g,"977","Розовое вино","Элджей, FEDUK","album11530439",219660,-1).firstConflict(),"old alias duration change even if extras absent");
  expect(!s(g,"977","Розовое вино","Элджей, FEDUK","album11530439",219660,-1).allowed(),"no stale-source reattachment");
  expect(s(g,"978","Розовое вино","Элджей, FEDUK","album11530439",246810,-1).allowed(),"different media alias recovers");
  System.out.println("PASS Test72SourceSnapshotConsistency");
 }
}

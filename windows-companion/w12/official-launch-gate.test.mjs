import {test} from "node:test";
import assert from "node:assert/strict";
import {assessOwnerLaunch,W12_OWNER,assessSyntheticFixture} from "./official-launch-gate.mjs";
const observation={windowsBuild:19045,architecture:"X64",exeVersion:"5.126.1.0",
  asarSha256:W12_OWNER.asarSha256,embeddedAsarIntegrity:"ENABLED",
  onlyLoadAppFromAsar:"ENABLED",resourcePresent:true,resourceMatches:true};
const ideal={observation,officialProcessRunning:false,singleInstancePolicyConfirmed:true,
  cleanProfileIsolationConfirmed:true,noAccountOrPrivateDataGuarantee:true,
  separateReversibleTestConsent:true};
test("W12 even ideal W10 proof cannot enable a real app launcher",()=>{
  const x=assessOwnerLaunch(ideal);
  for(const k of ["mayLaunchOfficial","mayOpenAuthenticatedRenderer",
    "mayEnableOfficialDebugger","mayModifyOfficialExeOrAsar"])
    assert.equal(x[k],false);
  assert.ok(x.blockers.includes("REAL_OFFICIAL_LAUNCH_NOT_IMPLEMENTED"));
});
test("W12 owner currently runs official client, so separate startup is blocked",()=>{
  const x=assessOwnerLaunch({...ideal,officialProcessRunning:true});
  assert.ok(x.blockers.includes("EXISTING_OFFICIAL_PROCESS_OR_UNKNOWN"));
});
test("W12 missing/untrusted observation always fails closed",()=>{
  for(const observation of [null,{},undefined,[],"W10 OK"]){
    const x=assessOwnerLaunch({...ideal,observation});
    assert.equal(x.mayLaunchOfficial,false);
    assert.ok(x.blockers.includes("NO_VERIFIED_OWNER_OBSERVATION")||
      x.blockers.includes("IDENTITY_NOT_OWNER_W10"));
  }
});
test("W12 changed archive, exe, integrity, OS identity always blocked",()=>{
  for(const patch of [{exeVersion:"5.126.2.0"},{asarSha256:"0".repeat(64)},
    {windowsBuild:26000},{embeddedAsarIntegrity:"DISABLED"},
    {resourceMatches:false},{resourcePresent:false}]){
    const x=assessOwnerLaunch({...ideal,observation:{...observation,...patch}});
    assert.equal(x.mayLaunchOfficial,false);
    assert.ok(x.blockers.some(y=>/IDENTITY|INTEGRITY/.test(y)));
  }
});
test("W12 unverified single-instance, profile, account, owner permission no-go",()=>{
  for(const key of ["singleInstancePolicyConfirmed","cleanProfileIsolationConfirmed",
      "noAccountOrPrivateDataGuarantee","separateReversibleTestConsent"]){
    const x=assessOwnerLaunch({...ideal,[key]:false});
    assert.equal(x.mayLaunchOfficial,false); assert.ok(x.blockers.length>1);
  }
});
test("W12 synthetic marker allows fixture only, never real official client",()=>{
  assert.equal(assessSyntheticFixture({fixtureMarker:"CELIKOM_W12_GENERATED_FIXTURE_ONLY",
    profileA:"A",profileB:"B"}).allowSyntheticLab,true);
  assert.equal(assessSyntheticFixture({fixtureMarker:"YANDEX_REAL_APP",
    profileA:"A",profileB:"B"}).allowSyntheticLab,false);
  assert.equal(assessSyntheticFixture({fixtureMarker:"CELIKOM_W12_GENERATED_FIXTURE_ONLY",
    profileA:"A",profileB:"A"}).allowSyntheticLab,false);
});

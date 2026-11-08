/**
 * W12 — no official executable launcher. All production checks fail closed.
 * W10 owner report proves installed signed ASAR integrity is ENABLED/MATCH.
 * Synthetic Electron tests cannot authorize launching an authenticated app.
 */
export const W12_OWNER = Object.freeze({
  windowsBuild:19045, architecture:"X64", exeVersion:"5.126.1.0",
  asarSha256:"5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215"
});
export function assessOwnerLaunch(request={}) {
  const blockers=[], o=request?.observation;
  if(!o || typeof o!=="object" || Array.isArray(o)) blockers.push("NO_VERIFIED_OWNER_OBSERVATION");
  else {
    if(o.windowsBuild!==W12_OWNER.windowsBuild ||
       o.architecture!==W12_OWNER.architecture ||
       o.exeVersion!==W12_OWNER.exeVersion ||
       o.asarSha256!==W12_OWNER.asarSha256)
       blockers.push("IDENTITY_NOT_OWNER_W10");
    if(o.embeddedAsarIntegrity!=="ENABLED" ||
       o.onlyLoadAppFromAsar!=="ENABLED" ||
       o.resourcePresent!==true || o.resourceMatches!==true)
       blockers.push("INTEGRITY_NOT_OWNER_W10");
  }
  if(request.officialProcessRunning!==false)
    blockers.push("EXISTING_OFFICIAL_PROCESS_OR_UNKNOWN");
  if(request.singleInstancePolicyConfirmed!==true)
    blockers.push("OFFICIAL_SINGLE_INSTANCE_BEHAVIOR_UNPROVEN");
  if(request.cleanProfileIsolationConfirmed!==true)
    blockers.push("OFFICIAL_PROFILE_ISOLATION_UNPROVEN");
  if(request.noAccountOrPrivateDataGuarantee!==true)
    blockers.push("NO_PRIVATE_DATA_GUARANTEE");
  if(request.separateReversibleTestConsent!==true)
    blockers.push("NO_TEST_SPECIFIC_OWNER_CONSENT");
  blockers.push("REAL_OFFICIAL_LAUNCH_NOT_IMPLEMENTED");
  return Object.freeze({
    decision:"NO_GO_OFFICIAL_CLIENT_LAUNCH",
    mayLaunchOfficial:false,mayOpenAuthenticatedRenderer:false,
    mayEnableOfficialDebugger:false,mayModifyOfficialExeOrAsar:false,
    installedVersionIntegrity:"ENFORCED_ASAR_V1",
    nextPermittedStep:"SYNTHETIC_SINGLE_INSTANCE_LAB_ONLY",
    blockers:Object.freeze([...new Set(blockers)])
  });
}
export function assessSyntheticFixture({fixtureMarker,profileA,profileB}={}) {
  return Object.freeze({
    allowSyntheticLab:fixtureMarker==="CELIKOM_W12_GENERATED_FIXTURE_ONLY" &&
      typeof profileA==="string" && typeof profileB==="string" &&
      profileA.length>0 && profileB.length>0 && profileA!==profileB,
    allowOfficialApp:false
  });
}

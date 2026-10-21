package pro.celikom.nativeprobe.identitydiag;
/** A delayed access/permission result cannot undo a later Stop or account change. */
final class StartIntent {
 long generation;boolean pending;
 long begin(){pending=true;return ++generation;}
 void cancel(){pending=false;generation++;}
 boolean current(long request){return pending&&request==generation;}
}

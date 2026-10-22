package pro.celikom.nativeprobe.identitydiag;
/** Smooth endpoints with complementary gains; no jump or gain boost at the join. */
final class TransitionMix {
 static float progress(long elapsed,long duration){float t=Math.max(0f,Math.min(1f,elapsed/(float)duration));return t*t*(3f-2f*t);}
}

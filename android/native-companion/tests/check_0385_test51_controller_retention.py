"""Test.51: a quiet buffering Yandex source must not cause forced reconnect."""
from pathlib import Path
src=(Path(__file__).resolve().parents[1]/"addon/src/pro/celikom/nativeprobe/identitydiag/ProbeService.java").read_text(encoding="utf-8")
begin=src.index("if(stateWatchdog.observeQuietBuffering(")
end=src.index("   emptySince=-1;",begin)
block=src[begin:end]
assert '"source_controller_quiet_buffering_observed"' in block
assert '"controllerRetained",true' in block
assert '"transportCommandSent",false' in block
for dangerous in ("c.release(", "connect(", "controller=null", "replacement.update(null)", "replacement.suspend(", "sourceBoundary(", "current=null", "return;"):
 assert dangerous not in block, "BUFFERING must not sever native Yandex connection: "+dangerous
assert 'if(c==null||!c.isConnected())' in src, "Actual disconnected-controller reconnect preserved"
assert '"source_controller_refresh"' in src, "Other guarded source-boundary logic preserved"
print("PASS: Test.51 connected BUFFERING is diagnostic only; real disconnect retains reconnect")

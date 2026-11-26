(() => {
  if (window.top !== window || window.__CELIKOM_MOBILE__) return;
  const adapter = window.__CELIKOM_YANDEX_ADAPTER_V1__.createAdapter(window);
  const guard = new window.__CELIKOM_ORIGINAL_GUARD_V1__.OriginalAudioGuard();
  let lease = null;
  const release = token => {
    if (token && lease?.token !== token) return false;
    const old=lease; guard.release(); lease = null;
    if(old) try { window.CelikomLease?.postMessage(JSON.stringify({released:old.token})); } catch (_) {}
    return true;
  };
  const valid = s => s?.track?.id && !s.track.ambiguous && s.track.confidence >= 100 &&
    s.player?.mediaId && s.player.readyState >= 2 && !s.player.ended &&
    Number.isFinite(s.player.duration) && s.track.metadata?.durationMs > 0 &&
    Math.abs(s.player.duration * 1000 - s.track.metadata.durationMs) <= 1500;
  const check = () => {
    if (!lease) return;
    const s = adapter.getSnapshot('android-watchdog');
    const e = adapter.getMediaElement(lease.mediaId);
    if (Date.now() > lease.deadline || !valid(s) || s.track.id !== lease.trackId ||
      s.player.mediaId !== lease.mediaId || !e || (e.currentSrc || e.src || '') !== lease.source ||
      s.player.paused || s.player.seeking || document.hidden) release();
  };
  adapter.mount({onSnapshot: check, onPlayerEvent: check});
  setInterval(check, 100);
  addEventListener('pagehide', () => release());
  document.addEventListener('visibilitychange', check);
  const snapshot = () => {
    check(); const s=adapter.getSnapshot('android');
    if (lease) lease.deadline=Date.now()+1500;
    return JSON.stringify({trackId:s.track?.id||null, confidence:s.track?.confidence||0,
      ambiguous:!!s.track?.ambiguous, canonicalMs:s.track?.metadata?.durationMs||0,
      mediaId:s.player?.mediaId||null, position:s.player?.currentTime||0,
      duration:s.player?.duration||0, paused:s.player?.paused!==false,
      seeking:!!s.player?.seeking, ended:!!s.player?.ended, readyState:s.player?.readyState||0,
      rate:s.player?.playbackRate||1, volume:guard.state().active?guard.state().volume:(s.player?.volume??1),
      muted:guard.state().active?guard.state().muted:!!s.player?.muted,
      guarded:!!lease, valid:!!valid(s)});
  };
  const engage = (trackId,mediaId,token) => {
    release(); const s=adapter.getSnapshot('android-engage');
    const e=adapter.getMediaElement(mediaId);
    if(!valid(s)||s.track.id!==trackId||s.player.mediaId!==mediaId||s.player.paused||s.player.seeking||!e) return false;
    try {
      guard.engage(e,mediaId,token);
      lease={trackId,mediaId,token,source:e.currentSrc||e.src||'',deadline:Date.now()+1500};
      return true;
    } catch (_) { release(); return false; }
  };
  Object.defineProperty(window,'__CELIKOM_MOBILE__',{value:Object.freeze({snapshot,engage,release}),writable:false});
})();

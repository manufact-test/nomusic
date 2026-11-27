(function registerReplacementController(root) {
  "use strict";
  const KEY = "__CELIKOM_REPLACEMENT_CONTROLLER_V1__";
  if (root[KEY]) return;
  class ReplacementController {
    constructor(bridge, environment, options = {}) {
      // Registration can precede dependencies during recovery injection. Resolve
      // them at construction, never capture an absent value in an immutable registry.
      const core = root.__CELIKOM_PLAYER_CORE_V1__;
      const ReplacementPlayer = root.__CELIKOM_REPLACEMENT_PLAYER_V1__?.ReplacementPlayer;
      const SyncEngine = root.__CELIKOM_SYNC_ENGINE_V1__?.SyncEngine;
      const FailOpenController = root.__CELIKOM_FAIL_OPEN_V1__?.FailOpenController;
      if (typeof core?.normalizeTrackId !== "function" || !ReplacementPlayer || !SyncEngine || !FailOpenController) {
        throw new Error("Playback runtime dependencies are not ready");
      }
      this.core = core;
      this.SyncEngine = SyncEngine;
      this.bridge = bridge;
      this.environment = environment;
      this.log = options.log || (() => {});
      this.createPlayer = options.createPlayer || ((onFatal) => new ReplacementPlayer(environment, onFatal));
      this.resolveAsset = options.resolveAsset || null;
      this.onEvent = options.onEvent || (() => {});
      this.negativeResolution = null;
      this.failOpen = new FailOpenController(bridge, this.log);
      this.enabled = false;
      this.suspended = false;
      this.retryBlock = null;
      this.networkRetries = 0;
      this.masterClock = null;
      this.testTrackId = null;
      this.snapshot = null;
      this.operation = null;
      this.generation = 0;
      this.phase = "IDLE";
      this.manualBypass = null;
      this.blockedTrackId = null;
      this.restorePending = null;
      this.destroyed = false;
      this.driftMs = null;
      this.lastError = null;
      this.policyRevision = 0;
      this.activationCount = 0;
      this.startupHistory = [];
      this.warmedAsset = null;
      this.restoreCount = 0;
      this.lastRestore = null;
      this.restoreHistory = [];
      this.authorizationRefreshCount = 0;
      this.playbackHistory = [];
      this.incidents = [];
      this.lastPlaybackShape = null;
      this.lastPlaybackSampleAt = 0;
    }
    recordPlayback(event, incident = false) {
      const operation = this.operation, master = this.snapshot?.player, audio = operation?.player?.audio;
      const sync = operation?.sync;
      const shape = [this.phase,operation?.generation,this.snapshot?.track?.id,master?.mediaId,
        master?.resourceRevision,master?.paused,master?.seeking,master?.readyState,
        this.snapshot?.guard?.active,audio?.paused,audio?.seeking,audio?.readyState,sync?.mode,sync?.seekCount].join("|");
      const at = Date.now();
      if (event === "sample" && shape === this.lastPlaybackShape && at-this.lastPlaybackSampleAt < 5000) return;
      this.lastPlaybackShape = shape; this.lastPlaybackSampleAt = at;
      const entry = {at,event,phase:this.phase,generation:operation?.generation || null,
        trackId:operation?.trackId || null,detectedTrackId:this.snapshot?.track?.id || null,
        master:master ? {mediaId:master.mediaId,revision:master.resourceRevision,timeMs:Math.round(master.currentTime*1000),
          paused:master.paused,seeking:master.seeking,readyState:master.readyState} : null,
        guard:Boolean(this.snapshot?.guard?.active),
        replacement:audio ? {timeMs:Math.round(audio.currentTime*1000),paused:audio.paused,seeking:Boolean(audio.seeking),
          readyState:audio.readyState,rate:audio.playbackRate} : null,
        synchronization:sync ? {mode:sync.mode,driftMs:sync.driftMs,seeks:sync.seekCount,lastCorrection:sync.lastCorrection} : null};
      this.playbackHistory.push(entry);
      if (this.playbackHistory.length > 180) this.playbackHistory.shift();
      if (incident) {
        this.incidents.push({at,event,context:this.playbackHistory.slice(-20),
          audio:operation?.player?.diagnostics?.() || null});
        if (this.incidents.length > 24) this.incidents.shift();
      }
    }
    publishPolicy(reset = false) {
      this.bridge.post?.("POLICY_UPDATE", {revision:++this.policyRevision,enabled:this.enabled&&!this.suspended&&!this.destroyed,holdIntro:true,reset:reset===true,
        testTrackId:this.testTrackId,bypassTrackId:this.manualBypass?.trackId||null,blockedTrackId:this.blockedTrackId,
        negative:this.negativeResolution});
    }
    configure(enabled, testTrackId, explicitStart = false) {
      const id = this.core.normalizeTrackId(testTrackId);
      const changed = this.testTrackId !== id || this.enabled !== enabled;
      this.enabled = enabled;
      this.testTrackId = id;
      if(explicitStart && this.operation)this.abort("explicit-retry");
      if (changed || explicitStart) { this.warmedAsset = null; this.networkRetries = 0; this.freshResolve = true; this.manualBypass = null; this.blockedTrackId = null; this.retryBlock = null; this.masterClock = null; if (!this.suspended) this.lastError = null; this.negativeResolution = null; }
      this.publishPolicy(changed||explicitStart);
      if (this.enabled && !this.suspended) this.warmPendingTrack();
      this.reconcile();
    }
    suspendAccess(suspended, reason) {
      if (this.suspended === suspended) { if (suspended) this.lastError = reason; this.publishPolicy(); return; }
      this.suspended = suspended;
      this.warmedAsset = null;
      this.publishPolicy();
      if (suspended) { this.suspendedError = this.lastError; this.abort(reason); this.lastError = reason; }
      else {
        if (["api_forbidden", "api_access_denied"].includes(this.suspendedError)) this.blockedTrackId = null;
        this.lastError = null; this.negativeResolution = null; this.masterClock = null; this.publishPolicy(); this.reconcile();
      }
    }
    eligible(snapshot = this.snapshot, minimumReadyState = 2) {
      const track = snapshot?.track;
      const player = snapshot?.player;
      const exactRoute = this.testTrackId ? track?.id === this.testTrackId : Boolean(this.resolveAsset && this.core.normalizeTrackId(track?.id));
      return this.enabled && !this.suspended && this.bridge.isHealthy() && exactRoute && !track?.ambiguous
        && track?.confidence >= 100 && player && !player.ended && player.readyState >= minimumReadyState
        && Number.isFinite(player.duration) && player.duration > 0
        && Math.abs(player.duration * 1000 - track.metadata?.durationMs) <= 1500
        && this.manualBypass?.trackId !== track.id && this.blockedTrackId !== track.id;
    }
    sameBoundResourceMetadataGap(operation, snapshot) {
      const track = snapshot?.track, player = snapshot?.player;
      const refreshPending = track?.evidence === "awaiting-track-refresh";
      const observed = track?.metadata || {}, bound = operation?.masterMetadata || {};
      const normalize = this.core.normalizeText;
      const metadataMatches = ["title", "artist"].every(key =>
        !observed[key] || !bound[key] || normalize(observed[key]) === normalize(bound[key]));
      return Boolean(operation && track && !track.id && (track.ambiguous !== true || refreshPending) && !track.playbackMismatch
        && metadataMatches && player && player.mediaId === operation.mediaId
        && Number.isSafeInteger(operation.resourceRevision)
        && player.resourceRevision === operation.resourceRevision
        && !player.ended && player.readyState >= 1 && Number.isFinite(player.duration)
        && Math.abs(player.duration * 1000 - operation.masterDurationMs) <= 1500);
    }
    update(snapshot, eventType = "snapshot") {
      if (!snapshot || this.destroyed) return;
      if (this.snapshot && snapshot.observedAt < this.snapshot.observedAt) return;
      const previousId = this.snapshot?.track?.id;
      this.snapshot = snapshot;
      if(this.operation && (eventType === "SEEK" || snapshot.player?.seeking)) this.operation.userSought=true;
      const id = snapshot.track?.id;
      const player = snapshot.player;
      const metadataGap = this.sameBoundResourceMetadataGap(this.operation, snapshot);
      // Keep tracking real progress during a metadata gap. Using the bound ID
      // avoids treating missing/reappearing metadata as native clock movement.
      const clockId = metadataGap ? this.operation.trackId : id;
      if (!this.masterClock || this.masterClock.id !== clockId || this.masterClock.mediaId !== player?.mediaId
        || Math.abs((player?.currentTime || 0) - this.masterClock.time) > 0.01 || player?.paused || player?.seeking || player?.readyState < 3) {
        this.masterClock = { id: clockId, mediaId: player?.mediaId, time: player?.currentTime || 0, advancedAt: Date.now() };
      }
      if (id && ((previousId && id !== previousId) || (this.manualBypass && id !== this.manualBypass.trackId) || (this.blockedTrackId && id !== this.blockedTrackId))) { this.networkRetries = 0; this.manualBypass = null; this.blockedTrackId = null; this.retryBlock = null; this.lastError = null; this.publishPolicy(); }
      if (eventType === "ENDED" && player?.ended === true) {
        // Natural completion releases this lease; it must never block the next song.
        this.abort("master-ended"); return;
      }
      if (eventType === "ERROR") { this.abort("master-error", true); return; }
      this.warmPendingTrack();
      this.reconcile(eventType === "SEEK");
      this.recordPlayback("sample");
    }
    warmPendingTrack() {
      // Resolve only the selected, confidently identified track while Yandex is
      // loading its native source. This does not construct audio or acquire a
      // guard. Actual preparation still needs the original eligibility checks.
      const snapshot = this.snapshot, track = snapshot?.track, player = snapshot?.player;
      const id = this.core.normalizeTrackId(track?.id);
      if (this.warmedAsset && (this.warmedAsset.trackId !== id
          || (this.warmedAsset.mediaId && player?.mediaId && this.warmedAsset.mediaId !== player.mediaId))) this.warmedAsset = null;
      if (this.warmedAsset && !this.warmedAsset.mediaId && player?.mediaId) this.warmedAsset.mediaId = player.mediaId;
      if (!this.enabled || this.suspended || this.destroyed || !this.bridge.isHealthy()
          || this.testTrackId || !this.resolveAsset || !id || track.ambiguous || track.confidence < 100
          || (player && player.ended) || this.manualBypass?.trackId === id || this.blockedTrackId === id
          || this.operation?.trackId === id || this.warmedAsset
          || (this.negativeResolution?.trackId === id && this.negativeResolution.until > Date.now())) return;
      if (this.eligible(snapshot)) return;
      // The selected Yandex track can be known several seconds before its native
      // audio element exists. Resolve only its authorized descriptor now; this
      // never creates audio, changes playback, or acquires an original guard.
      if (player && player.readyState > 0 && Number.isFinite(player.duration)
          && snapshot.guard?.transitioning !== true) return;
      const warm = {trackId:id, mediaId:player?.mediaId || null, startedAt:Date.now(),
        fresh:this.networkRetries > 0 || this.freshResolve === true};
      this.warmedAsset = warm;
      // Handle rejection immediately: an obsolete warm-up must never become an
      // unhandled rejection or affect a different song's playback.
      warm.result = Promise.resolve().then(() => this.resolveAsset(id, {fresh:warm.fresh}))
        .then(asset => ({asset}), error => ({error}));
    }
    current(operation) { return !this.destroyed && this.operation === operation && this.generation === operation.generation; }
    releaseIntroWait(token) {
      const operation = this.operation;
      if (this.phase !== "PREPARING" || !operation || !this.current(operation) || operation.token !== token) return false;
      operation.generation = ++this.generation;
      operation.token = `${this.bridge.sessionId}:${operation.generation}`;
      return true;
    }
    event(name, properties) {
      try { Promise.resolve(this.onEvent(name, properties)).catch(() => undefined); }
      catch (_error) { /* best-effort telemetry is not a playback dependency */ }
    }
    reconcile(forceSync = false) {
      if (this.destroyed || this.restorePending) return;
      // Resource continuity never overrides Stop, access suspension, or a lost
      // bridge. Apply these controls before tolerating missing track metadata.
      if (!this.enabled || this.suspended || !this.bridge.isHealthy()) {
        if (this.operation) this.abort("state-changed");
        return;
      }
      if (this.retryBlock && Date.now() >= this.retryBlock.at && this.snapshot?.observedAt > this.retryBlock.observedAt
        && Date.now() - this.snapshot.observedAt < 3000 && this.bridge.isHealthy() && this.snapshot.player?.readyState >= 3
        && (this.retryBlock.reason !== "master-clock-stalled" || Math.abs(this.snapshot.player.currentTime - this.retryBlock.time) > 0.01)) {
        this.blockedTrackId = null; this.retryBlock = null; this.lastError = null; this.publishPolicy();
      }
      const operation = this.operation;
      const matching = operation && operation.trackId === this.snapshot?.track?.id && operation.mediaId === this.snapshot?.player?.mediaId;
      if (this.sameBoundResourceMetadataGap(operation, this.snapshot)) {
        // Yandex may briefly clear MediaMetadata while the exact same native
        // resource keeps playing. Preserve its already-validated replacement;
        // source revision, media element and duration still fence this grace.
        if (this.phase === "REPLACEMENT_ACTIVE" && operation.player) {
          const player = this.snapshot.player;
          if (player.paused || player.seeking || player.readyState < 3) operation.player.pause();
          else {
            try { this.driftMs = operation.sync.sync(operation.player, this.snapshot, forceSync); }
            catch (error) { this.abort(error.message, true); }
          }
        }
        return;
      }
      // A bound, already guarded master can temporarily have only metadata while
      // seeking/buffering. Keep the lease and pause replacement; admission still
      // requires current data, and emptied/changed/ambiguous masters fail open.
      /* Warm a validated paused beginning before native playback.
         Mid-song buffering and seeks retain the existing admission rules. */
      const earlyIntro = !operation && !this.snapshot?.guard?.transitioning && this.snapshot?.player?.paused
        && !this.snapshot.player.seeking && this.snapshot.player.currentTime <= 0.25;
      const minimumReadyState = (operation && matching) || earlyIntro ? 1 : 2;
      if (!this.eligible(this.snapshot, minimumReadyState) || (operation && !matching)) {
        if (operation) this.abort("state-changed");
        return;
      }
      if (!operation) {
        if (this.negativeResolution?.trackId === this.snapshot.track.id && this.negativeResolution.until > Date.now()) return;
        void this.prepare(); return;
      }
      if (this.phase === "PREPARING" && operation.loaded && !operation.activating && this.eligible()) {
        void this.activate(operation);
      }
      if (this.phase === "REPLACEMENT_ACTIVE") {
        if (!operation.asset.demoLoop && operation.asset.expiresAt<=Date.now()) {
          if(this.snapshot.player.paused){operation.player.pause();return;}
          this.abort("audio-token-expired",true);return;
        }
        try { this.driftMs = operation.sync.sync(operation.player, this.snapshot, forceSync); }
        catch (error) { this.abort(error.message, true); }
      }
    }
    async prepare() {
      const snapshot = this.snapshot;
      const operation = { initialMasterTime:snapshot.player.currentTime,startedAt:Date.now(),stage:"resolving",generation: ++this.generation, token: `${this.bridge.sessionId}:${this.generation}`, trackId: snapshot.track.id, mediaId: snapshot.player.mediaId, resourceRevision:Number.isSafeInteger(snapshot.player.resourceRevision)?snapshot.player.resourceRevision:null, masterDurationMs:Math.round(snapshot.track.metadata?.durationMs || snapshot.player.duration*1000), masterMetadata:{title:String(snapshot.track.metadata?.title||""),artist:String(snapshot.track.metadata?.artist||"")}, sync: new this.SyncEngine(), player: null };
      operation.wasUnavailable = this.negativeResolution?.trackId === operation.trackId;
      this.operation = operation;
      this.phase = "PREPARING";
      this.log(`PREPARING · ${operation.trackId}`);
      try {
        const warm = this.warmedAsset;
        this.warmedAsset = null;
        const useWarm = !this.testTrackId && warm?.trackId === operation.trackId
          && (!warm.mediaId || warm.mediaId === operation.mediaId) && Date.now()-warm.startedAt <= 5000
          && (!(this.networkRetries > 0 || this.freshResolve === true) || warm.fresh);
        if (useWarm) {
          const result = await warm.result;
          if (!this.current(operation)) return;
          if (result.error) throw result.error;
          // Never extend a signed grant's lifetime by warming it.
          if (!result.asset?.found || result.asset.expiresAt > Date.now()+1000) {
            operation.asset = result.asset;
            operation.warmLeadMs = operation.startedAt-warm.startedAt;
          }
        }
        if (!operation.asset) operation.asset = this.testTrackId
          ? { found: true, url: this.environment.chrome.runtime.getURL("assets/test-audio.mp3"), demoLoop: true }
          : await this.resolveAsset(operation.trackId, { fresh: this.networkRetries > 0 || this.freshResolve === true });
        this.freshResolve = false;
        if (!this.current(operation)) return;
        if (!operation.asset?.found) {
          this.negativeResolution = { trackId: operation.trackId, until: Date.now() + Math.min(60000, Math.max(5000, operation.asset?.retryAfterMs || 15000)) };
          this.publishPolicy();
          if (this.snapshot?.guard?.transitioning) await this.bridge.request("GUARD_TRANSITION_END", {token:operation.token,trackId:operation.trackId,mediaId:operation.mediaId});
          if (!this.current(operation)) return;
          this.operation = null; this.phase = "IDLE"; this.log(`NO_REPLACEMENT · ${operation.trackId}`); return;
        }
        if (!operation.asset.demoLoop && (!Number.isFinite(operation.asset.durationMs)
          || Math.abs(operation.asset.durationMs - snapshot.track.metadata.durationMs) > 1500 || operation.asset.expiresAt <= Date.now())) {
          throw new Error("replacement_duration_or_token_invalid");
        }
        if (!operation.asset.demoLoop) this.event("replacement_available", { service: "yandex" });
        operation.completeJoin = operation.wasUnavailable && !operation.asset.demoLoop && operation.asset.mimeType === "audio/mpeg"
          && this.snapshot?.player?.currentTime > 0.25;
        if(operation.completeJoin && this.snapshot?.guard?.transitioning) {
          await this.bridge.request("GUARD_TRANSITION_END",{token:operation.token,trackId:operation.trackId,mediaId:operation.mediaId});
          if(!this.current(operation))return;
          this.update(await this.bridge.getSnapshot());
          if(!this.current(operation))return;
        }
        if (!operation.completeJoin && this.snapshot?.guard?.transitioning && this.eligible()) {
          await this.bridge.request("GUARD_ENGAGE", {token:operation.token,trackId:operation.trackId,mediaId:operation.mediaId,preparing:true});
          if (!this.current(operation)) { this.bridge.post("RELEASE_NOW", {token:operation.token}); return; }
        }
        operation.resolvedAt = Date.now();
        operation.stage="loading";
        operation.player = this.createPlayer((reason, detail) => { if (this.current(operation)) this.abort(reason, true, detail); });
        if(operation.player.audio?.dataset)operation.player.audio.dataset.celikomTrackId=operation.trackId;
        await operation.player.prepare(operation.asset, {completeMp3:operation.completeJoin});
        if (!operation.asset.demoLoop && Math.abs(operation.player.audio.duration * 1000 - operation.asset.durationMs) > 1500) throw new Error("replacement_duration_mismatch");
        if (!this.current(operation)) return;
        operation.loadedAt = Date.now();
        operation.loaded = true;
        await this.activate(operation);
      } catch (error) { if (this.current(operation)) this.abort(error.message, true, error.streamDetail || null); }
    }
    async activate(operation) {
      // A seek changes readiness while preserving this track/media binding.
      // Retain its in-flight download and activate once a fresh master is ready.
      if (!this.current(operation) || operation.activating || !this.eligible()) return;
      operation.activating = true;
      try {
        this.update(await this.bridge.getSnapshot());
        if (!this.current(operation) || !this.eligible()) return;
        if(operation.completeJoin && !operation.joinAligned) {
          operation.stage="aligning-complete-file";
          await operation.player.prepareCompleteJoin(this.snapshot, async()=>{
            if(!this.current(operation))throw new Error("Replacement cancelled");
            this.update(await this.bridge.getSnapshot());
            if(!this.current(operation))throw new Error("Replacement cancelled");
            if(!this.eligible())throw new Error("complete-join-timeout");
            return this.snapshot;
          });
          if(!this.current(operation))return;
          this.update(await this.bridge.getSnapshot());
          if(!this.current(operation)||!this.eligible())return;
          const {projectTime,targetTime,driftAt}=root.__CELIKOM_SYNC_ENGINE_V1__,audio=operation.player.audio;
          const target=targetTime(projectTime(this.snapshot.player,this.snapshot.observedAt,Date.now()),audio.duration,false);
          if(this.snapshot.player.seeking||Math.abs(driftAt(audio.currentTime,target,audio.duration,false))>100)return;
          operation.joinAligned=true;
        }
        if (!operation.completeJoin && (operation.initialMasterTime > 0.25 || this.snapshot.player.currentTime > 5 || operation.userSought)
            && !operation.joinAligned && typeof operation.player.prepareMidSongPosition === "function") {
          operation.stage="aligning-mid-song";
          const aligned=await operation.player.prepareMidSongPosition(this.snapshot,async()=>{
            if(!this.current(operation))throw new Error("Replacement cancelled");
            this.update(await this.bridge.getSnapshot());
            if(!this.current(operation))throw new Error("Replacement cancelled");
            return this.snapshot;
          });
          if(!this.current(operation))return;
          if(!this.eligible()||!aligned)return;
          this.update(await this.bridge.getSnapshot());
          if(!this.current(operation)||!this.eligible())return;
          operation.joinAligned=true;
        }
        if (!operation.completeJoin && operation.initialMasterTime<=0.25
            && this.snapshot.player.currentTime>0.25 && this.snapshot.player.currentTime<=5
            && !operation.userSought && !operation.joinAligned
            && typeof operation.player.prepareIntroPosition === "function") {
          operation.stage="aligning-start";
          const aligned=await operation.player.prepareIntroPosition(this.snapshot,async()=>{
            if(!this.current(operation))throw new Error("Replacement cancelled");
            this.update(await this.bridge.getSnapshot());
            if(!this.current(operation))throw new Error("Replacement cancelled");
            return this.snapshot;
          });
          if(!this.current(operation)||!this.eligible()||!aligned)return;
          operation.joinAligned=true;
        }
        operation.stage="guarding";
        const guard = await this.bridge.request("GUARD_ENGAGE", { token: operation.token, trackId: operation.trackId, mediaId: operation.mediaId });
        if (!this.current(operation)) { this.bridge.post("RELEASE_NOW", { token: operation.token }); return; }
        this.update(guard.snapshot);
        if (!this.current(operation) || !this.eligible(this.snapshot, 1)) { this.abort("guard-state-changed"); return; }
        this.phase = "REPLACEMENT_ACTIVE";
        this.activationCount++;
        /* Bounded timings retain each recent join without URLs or credentials.
           Activation is a controller milestone, not proof of audible output. */
        this.startupHistory.push({trackId:operation.trackId, at:Date.now(),
          prepareMs:Date.now()-operation.startedAt, warmLeadMs:operation.warmLeadMs || 0,
          resolveMs:operation.resolvedAt-operation.startedAt,
          loadMs:operation.loadedAt-operation.resolvedAt,
          masterTimeMs:Math.round(this.snapshot.player.currentTime*1000),
          alignmentMs:Math.max(0,Date.now()-operation.loadedAt),
          audioPreparation:operation.player.preparationTiming||null});
        if(this.startupHistory.length>48)this.startupHistory.shift();
        if (!operation.asset.demoLoop) this.event("replacement_started", { service: "yandex" });
        this.lastError = null;
        this.log(`REPLACEMENT_ACTIVE · ${operation.trackId}`);
        this.reconcile(!operation.joinAligned);
      } catch (error) { if (this.current(operation)) this.abort(error.message, true, error.streamDetail || null); }
      finally { operation.activating = false; }
    }
    abort(reason, blockTrack = false, detail = null) {
      const operation = this.operation;
      if (blockTrack) { this.blockedTrackId = operation?.trackId || this.snapshot?.track?.id; this.lastError = reason; this.publishPolicy(); }
      const transientNetwork = ["complete-join-timeout", "mid-song-join-timeout", "remote-stream-route-blocked", "remote-stream-network", "remote-stream-timeout", "replacement-load-timeout", "api_network_error", "api_server_error", "api_unavailable"].includes(reason)
        || (reason === "remote-stream-http" && [429, 500, 502, 503, 504].includes(detail?.httpStatus))
        || (reason === "replacement-media-error" && detail?.mediaErrorCode === 2);
      if (blockTrack && (["bridge-timeout", "bridge-unhealthy", "snapshot-stale", "master-clock-stalled", "master-error", "audio-token-expired", "guard-lost:master-error"].includes(reason)
        || transientNetwork || detail?.reason === "media-source-changed")) {
        const delay = transientNetwork ? Math.min(60000, 5000 * 2 ** Math.min(this.networkRetries++, 4)) : 5000;
        this.retryBlock = { at: Date.now() + delay, observedAt: this.snapshot?.observedAt || 0, reason, time: this.snapshot?.player?.currentTime || 0 };
      }
      if (!operation) return;
      const completed = reason === "master-ended" || detail?.reason === "master-ended";
      if (operation.asset && !operation.asset.demoLoop && completed) this.event("replacement_completed", { service: "yandex" });
      else if (operation.asset && !operation.asset.demoLoop && !["manual-original", "state-changed", "controller-destroyed", "explicit-retry"].includes(reason)) this.event("fail_open", { service: "yandex", error_code: reason === "api_unavailable" ? "api_unavailable" : reason.startsWith("guard-lost:") ? "binding_changed" : "unknown" });
      const nearEnd = this.snapshot?.player && Number.isFinite(this.snapshot.player.duration)
        && this.snapshot.player.duration-this.snapshot.player.currentTime <= 0.35;
      const classification = completed || (reason === "replacement-ended" && nearEnd) ? "completion"
        : reason === "state-changed" && operation.trackId !== this.snapshot?.track?.id ? "track-change"
        : ["manual-original","controller-destroyed","explicit-retry","state-changed"].includes(reason) ? "control" : "interruption";
      this.recordPlayback(`restore:${reason}`, classification === "interruption");
      this.restoreCount++;
      this.lastRestore = {
        reason, detail, classification, requestedAt: Date.now(), trackId: operation.trackId, mediaId: operation.mediaId,
        detectedTrackId: this.snapshot?.track?.id || null, detectedMediaId: this.snapshot?.player?.mediaId || null,
        readyState: this.snapshot?.player?.readyState ?? null, seeking: Boolean(this.snapshot?.player?.seeking),
        snapshotReason: this.snapshot?.reason || null
      };
      this.restoreHistory.push(this.lastRestore);
      if (this.restoreHistory.length > 48) this.restoreHistory.shift();
      ++this.generation;
      this.operation = null;
      this.phase = "RESTORING";
      this.driftMs = null;
      this.log(`RESTORING · ${reason}`);
      const pending = this.failOpen.restore(operation, reason);
      this.restorePending = pending;
      void pending.finally(() => {
        if (this.restorePending !== pending) return;
        this.restorePending = null;
        this.phase = "IDLE";
        this.log("IDLE · original restored/release requested");
        this.reconcile();
      });
    }
    manualRestore() {
      this.warmedAsset = null;
      const trackId = this.snapshot?.track?.id || this.operation?.trackId;
      if (trackId) this.manualBypass = { trackId, requestedAt: Date.now() };
      this.publishPolicy();
      this.abort("manual-original");
    }
    canRecoverConnection() {
      const reason=this.retryBlock?.reason||this.lastError;
      return ["api_network_error","api_server_error","api_unavailable","remote-stream-network","remote-stream-route-blocked",
        "remote-stream-timeout","replacement-load-timeout","mid-song-join-timeout","bridge-timeout","bridge-unhealthy","snapshot-stale"].includes(reason)
        ||(reason==="remote-stream-http"&&Boolean(this.retryBlock));
    }
    recoverConnection() {
      if(!this.enabled||this.suspended||this.destroyed||this.operation||this.manualBypass||!this.bridge.isHealthy()||!this.canRecoverConnection())return;
      this.blockedTrackId=null;this.retryBlock=null;this.lastError=null;this.networkRetries=0;this.freshResolve=true;
      this.publishPolicy();this.reconcile();
    }
    renewPausedAuthorization() {
      const operation=this.operation;
      if (!operation || this.phase!=="REPLACEMENT_ACTIVE" || operation.renewing
          || operation.renewAfter>Date.now() || operation.asset.demoLoop
          || operation.asset.expiresAt>Date.now()+90000 || !this.snapshot?.player?.paused
          || !this.eligible() || !operation.player.canRevalidateAuthorization?.()) return;
      operation.renewing=true;
      void (async()=>{
        const asset=await this.resolveAsset(operation.trackId,{fresh:true});
        if(!this.current(operation))return;
        if(asset?.found===false){
          this.negativeResolution={trackId:operation.trackId,until:Date.now()+Math.min(60000,Math.max(5000,asset.retryAfterMs||15000))};
          this.publishPolicy();this.abort("replacement-no-longer-available");return;
        }
        if(!asset?.found || asset.expiresAt<=Date.now()+1000
          ||Math.abs(asset.durationMs-this.snapshot.track.metadata.durationMs)>1500)
          throw new Error("replacement_duration_or_token_invalid");
        const same=await operation.player.revalidateAuthorization(asset);
        if(!this.current(operation))return;
        if(!same){this.abort("paused-asset-changed");return;}
        operation.asset=asset;this.authorizationRefreshCount++;
        this.log(`PAUSED_ASSET_REVALIDATED · ${operation.trackId}`);
      })().catch(error=>{
        if(!this.current(operation))return;
        operation.renewAfter=Date.now()+5000;
        if(["api_forbidden","api_access_denied","api_access_missing"].includes(error.message) || [401,403,404].includes(error.streamDetail?.httpStatus)
            ||operation.asset.expiresAt<=Date.now())this.abort(error.message,true,error.streamDetail||null);
      }).finally(()=>{operation.renewing=false;});
    }
    tick() {
      if (this.operation && this.masterClock && !this.snapshot.player.paused && !this.snapshot.player.seeking
        && this.snapshot.player.readyState >= 3 && !this.environment.document.hidden && Date.now() - this.masterClock.advancedAt > 4000) {
        this.abort("master-clock-stalled", true); return;
      }
      if (!this.bridge.isHealthy() && this.operation) { this.abort("bridge-unhealthy", true); return; }
      this.renewPausedAuthorization();
      if (this.operation?.asset && !this.operation.asset.demoLoop && this.operation.asset.expiresAt <= Date.now()
          && (!this.snapshot.player.paused || !this.operation.renewing)) { this.abort("audio-token-expired", true); return; }
      if (this.operation && this.snapshot.player.readyState >= 3 && !this.snapshot.player.paused && !this.snapshot.player.seeking
        && Date.now() - this.snapshot.observedAt > 3000 && !this.environment.document.hidden) {
        this.abort("snapshot-stale", true); return;
      }
      this.reconcile();
    }
    destroy() { this.warmedAsset = null; this.destroyed = true; this.publishPolicy(); this.abort("controller-destroyed"); }
  }
  Object.defineProperty(root, KEY, { value: Object.freeze({ ReplacementController }), writable: false });
})(globalThis);


export const PLAYER_EVENT_TYPES = [
  "TRACK_CHANGED",
  "PLAY",
  "PAUSE",
  "SEEK",
  "TIME_UPDATE",
  "VOLUME_CHANGED",
  "RATE_CHANGED",
  "METADATA_CHANGED",
  "ENDED",
  "ERROR"
] as const;

export type PlayerEventType = typeof PLAYER_EVENT_TYPES[number];

export interface TrackCandidate {
  id: string;
  score: number;
  source: string;
  evidence: string;
}

export interface TrackMetadata {
  title: string;
  artist: string;
  album: string;
  coverUri: string;
  durationMs: number;
}

export interface DetectedTrack {
  id: string | null;
  confidence: number;
  source: string | null;
  evidence: string;
  ambiguous: boolean;
  candidates: TrackCandidate[];
  metadata: TrackMetadata;
  catalogSize: number;
}

export interface PlayerState {
  mediaId: string;
  tag: "audio" | "video";
  paused: boolean;
  ended: boolean;
  seeking: boolean;
  currentTime: number;
  duration: number | null;
  playbackRate: number;
  volume: number;
  muted: boolean;
  readyState: number;
  networkState: number;
  source: string;
  connected: boolean;
}

export interface PlayerSnapshot {
  service: "yandex-music";
  reason: string;
  observedAt: number;
  route: string;
  track: DetectedTrack;
  player: PlayerState | null;
  mediaCandidates: Array<Record<string, unknown>>;
  adapterVersion: string;
}

export interface NormalizedPlayerEvent {
  type: PlayerEventType;
  nativeEvent: string;
  sequence: number;
  observedAt: number;
  trackId: string | null;
  mediaId: string | null;
  snapshot: PlayerSnapshot;
}

export interface ServiceAdapterSink {
  onSnapshot(snapshot: PlayerSnapshot): void;
  onPlayerEvent(event: Omit<NormalizedPlayerEvent, "sequence">): void;
}

export interface ServiceAdapter {
  readonly service: "yandex-music";
  readonly mounted: boolean;
  mount(sink: ServiceAdapterSink): void;
  unmount(): void;
  getSnapshot(reason?: string): PlayerSnapshot;
}


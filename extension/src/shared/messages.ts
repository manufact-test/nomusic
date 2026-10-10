export const COMMANDS = {
  getStatus: "CELIKOM_STATUS_GET",
  setEnabled: "CELIKOM_ENABLED_SET",
  setTestTrack: "CELIKOM_TEST_TRACK_SET",
  retryReplacement: "CELIKOM_REPLACEMENT_RETRY",
  restoreOriginal: "CELIKOM_RESTORE_ORIGINAL",
  controllerPing: "CELIKOM_CONTROLLER_PING",
  getControllerStatus: "CELIKOM_CONTROLLER_STATUS_GET"
} as const;

export type Command = typeof COMMANDS[keyof typeof COMMANDS];

export interface ExtensionState {
  enabled: boolean;
  phase: "STOPPED" | "CONNECTING" | "OBSERVING" | "READY" | "ERROR" | "PREPARING" | "REPLACEMENT_ACTIVE" | "RESTORING";
  version: string;
  settings?: { testTrackId: string };
  accessError?: string;
  manualBypass?: { trackId: string } | null;
  replacementError?: string | null;
  connection?: {
    controllerPresent: boolean;
    recovered: boolean;
    error: string | null;
    detail: string | null;
  };
  track?: {
    id: string | null;
    confidence: number;
    source: string | null;
    ambiguous: boolean;
    metadata?: {
      title?: string;
      artist?: string;
      album?: string;
      durationMs?: number;
    };
  } | null;
  bridge?: {
    ready: boolean;
    healthy: boolean;
  };
}

export function normalizeEnabled(value: unknown): boolean {
  return value === true;
}

export function isCommand(value: unknown): value is Command {
  return typeof value === "string" && Object.values(COMMANDS).includes(value as Command);
}

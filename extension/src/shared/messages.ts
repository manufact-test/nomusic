export const COMMANDS = {
  getStatus: "CELIKOM_STATUS_GET",
  setEnabled: "CELIKOM_ENABLED_SET",
  restoreOriginal: "CELIKOM_RESTORE_ORIGINAL",
  controllerPing: "CELIKOM_CONTROLLER_PING",
  getControllerStatus: "CELIKOM_CONTROLLER_STATUS_GET"
} as const;

export type Command = typeof COMMANDS[keyof typeof COMMANDS];

export interface ExtensionState {
  enabled: boolean;
  phase: "STOPPED" | "CONNECTING" | "OBSERVING" | "READY";
  version: string;
  track?: {
    id: string | null;
    confidence: number;
    source: string | null;
    ambiguous: boolean;
    metadata?: {
      title?: string;
      artist?: string;
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

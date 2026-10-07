export const COMMANDS = {
  getStatus: "CELIKOM_STATUS_GET",
  setEnabled: "CELIKOM_ENABLED_SET",
  restoreOriginal: "CELIKOM_RESTORE_ORIGINAL",
  controllerPing: "CELIKOM_CONTROLLER_PING"
} as const;

export type Command = typeof COMMANDS[keyof typeof COMMANDS];

export interface ExtensionState {
  enabled: boolean;
  phase: "IDLE" | "STOPPED";
  version: string;
}

export function normalizeEnabled(value: unknown): boolean {
  return value === true;
}

export function isCommand(value: unknown): value is Command {
  return typeof value === "string" && Object.values(COMMANDS).includes(value as Command);
}

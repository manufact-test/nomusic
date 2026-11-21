import type { ExtensionState } from "../shared/messages.js";
export function playbackPresentation(state: ExtensionState) {
  const waiting=state.phase==="PREPARING";
  const retry=state.phase==="ERROR"||Boolean(state.replacementError||state.manualBypass||state.suspended)
    ||(waiting&&(state.preparation?.elapsedMs??0)>=10000);
  const label=waiting ? state.preparation?.stage==="loading"?"Загружаем аудио…":"Проверяем подмену…"
    :state.phase==="READY"?"Включён · играет оригинал":null;
  return {label,retry,startDisabled:state.enabled&&!retry,startLabel:retry?"Повторить":"Старт"};
}

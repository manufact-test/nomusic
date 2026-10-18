// Device-local bounded upload history. Never record audio, names, credentials or URLs.
export const KEY = "celikom_upload_journal_v1";
const validId = value => typeof value === "string" &&
  /^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(value);
export function createUploadJournal(storage) {
  let pending = Promise.resolve();
  async function read() {
    try {
      const value = (await storage?.get(KEY))?.[KEY];
      const cutoff = Date.now() - 7 * 86400000;
      return Array.isArray(value) ? value.filter(item => item &&
        validId(item.id) && Number.isFinite(item.updatedAt) && item.updatedAt > cutoff).slice(0, 25) : [];
    } catch { return []; }
  }
  function record(id, phase, details = {}) {
    if (!storage || !validId(id) || !/^[a-z_]{2,30}$/.test(phase)) return Promise.resolve();
    pending = pending.catch(() => {}).then(async () => {
      const all = await read(), previous = all.find(item => item.id === id), now = Date.now();
      const event = {at: now, phase};
      if (Number.isSafeInteger(details.sent) && details.sent >= 0) event.sent = details.sent;
      if (Number.isInteger(details.percent) && details.percent >= 0 && details.percent <= 100) event.percent = details.percent;
      if (Number.isInteger(details.httpStatus) && details.httpStatus >= 0 && details.httpStatus <= 599) event.httpStatus = details.httpStatus;
      if (typeof details.code === "string" && /^[a-z0-9_]{2,40}$/.test(details.code)) event.code = details.code;
      const current = {
        id, startedAt: previous?.startedAt || now, updatedAt: now,
        trackId: previous?.trackId || (/^[1-9]\d{0,23}$/.test(details.trackId || "") ? details.trackId : null),
        bytes: previous?.bytes || (Number.isSafeInteger(details.bytes) && details.bytes >= 0 ? details.bytes : null),
        events: [...(previous?.events || []), event].slice(-20)
      };
      await storage.set({[KEY]: [current, ...all.filter(item => item.id !== id)].slice(0, 25)});
    }).catch(() => {}); // Never block a submit due to diagnostic storage failure.
    return pending;
  }
  async function snapshot() { await pending.catch(() => {}); return read(); }
  return {record, snapshot};
}

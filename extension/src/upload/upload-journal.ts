export const KEY = "celikom_upload_journal_v1";
export function createUploadJournal(storage) {
  let pending = Promise.resolve();
  async function read() {
    try { const value = (await storage?.get(KEY))?.[KEY]; return Array.isArray(value) ? value : []; }
    catch { return []; }
  }
  function record(id, phase, details = {}) {
    if (!storage || !/^[a-f0-9-]{36}$/i.test(id)) return Promise.resolve();
    pending = pending.catch(() => {}).then(async () => {
      const existing = await read(), previous = existing.find(item => item.id === id);
      const event = {phase, time: Date.now(), ...details};
      const current = {id, startedAt: previous?.startedAt || Date.now(), events: [...(previous?.events || []), event].slice(-20)};
      await storage.set({[KEY]: [current, ...existing.filter(item => item.id !== id)].slice(0, 25)});
    }).catch(() => {});
    return pending;
  }
  async function snapshot() { await pending; return read(); }
  return {record, snapshot};
}

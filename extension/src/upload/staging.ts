// Chrome extension origin IndexedDB. File contents are staged only for the
// current explicitly submitted upload, never sent through JSON messaging.
const DB = "celikom-ephemeral-uploads";
const STORE = "audio";
function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB, 1);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(STORE)) request.result.createObjectStore(STORE);
    };
    request.onerror = () => reject(new Error("upload_staging_unavailable"));
    request.onsuccess = () => resolve(request.result);
  });
}
async function transaction(mode, action) {
  const db = await openDatabase();
  try {
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, mode);
      const request = action(tx.objectStore(STORE));
      let result;
      request.onsuccess = () => { result = request.result; };
      tx.oncomplete = () => resolve(result);
      tx.onerror = () => reject(new Error("upload_staging_unavailable"));
      tx.onabort = () => reject(new Error("upload_staging_unavailable"));
    });
  } finally { db.close(); }
}
export async function stageUploadFile(id, file) {
  if (!/^[a-f0-9-]{36}$/i.test(id) || !(file instanceof Blob) || file.size < 1024 || file.size > 31457280)
    throw new Error("invalid_upload_file");
  await transaction("readwrite", store => store.put({ file, at: Date.now() }, id));
}
export async function readStagedUpload(id) {
  const record = await transaction("readonly", store => store.get(id));
  if (!record || !(record.file instanceof Blob) || !Number.isFinite(record.at) ||
      Date.now() - record.at > 1800000) throw new Error("upload_staging_expired");
  return record.file;
}
export async function deleteStagedUpload(id) {
  if (/^[a-f0-9-]{36}$/i.test(id)) await transaction("readwrite", store => store.delete(id));
}

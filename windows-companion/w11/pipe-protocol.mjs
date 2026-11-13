/**
 * W11: Chromium DevTools pipe client for a disposable synthetic fixture ONLY.
 * Chrome reads fd3; writes fd4; messages are UTF8 JSON terminated by NUL.
 * This is a high-privilege protocol, NOT suitable for arbitrary user sessions.
 */
export function createPipeTransport(writer, reader, { maxMessage = 4_000_000 } = {}) {
  if (!writer || !reader || typeof writer.write !== "function") throw Error("W11_BAD_PIPES");
  const pending = new Map();
  let nextId = 0, backlog = Buffer.alloc(0), closed = false;

  function rejectPending(reason) {
    if (closed) return;
    closed = true;
    for (const [, job] of pending) {
      clearTimeout(job.timer);
      job.reject(Error(reason));
    }
    pending.clear();
  }
  reader.on("data", chunk => {
    if (closed) return;
    backlog = Buffer.concat([backlog, chunk]);
    if (backlog.length > maxMessage && !backlog.includes(0)) {
      rejectPending("W11_FRAME_TOO_LARGE");
      return;
    }
    for (let end; (end = backlog.indexOf(0)) >= 0;) {
      const data = backlog.subarray(0, end);
      backlog = backlog.subarray(end + 1);
      if (data.length > maxMessage) {
        rejectPending("W11_FRAME_TOO_LARGE");
        return;
      }
      let message;
      try { message = JSON.parse(data.toString("utf8")); }
      catch { rejectPending("W11_INVALID_CDP_FRAME"); return; }
      if (!Number.isInteger(message?.id) || !pending.has(message.id)) continue;
      const wait = pending.get(message.id);
      if (wait.sessionId && wait.sessionId !== message.sessionId) {
        rejectPending("W11_SESSION_ID_MISMATCH");
        return;
      }
      clearTimeout(wait.timer);
      pending.delete(message.id);
      if (message.error) wait.reject(Error("W11_CDP_ERROR_" + Number(message.error.code)));
      else wait.resolve(message.result);
    }
    if (backlog.length > maxMessage) rejectPending("W11_FRAME_TOO_LARGE");
  });
  reader.on("error", () => rejectPending("W11_READ_FAILURE"));
  reader.on("close", () => rejectPending("W11_READ_CLOSED"));
  writer.on("error", () => rejectPending("W11_WRITE_FAILURE"));

  return Object.freeze({
    send(method, params = {}, { sessionId, timeoutMs = 15000 } = {}) {
      if (!["Browser.getVersion", "Target.getTargets", "Target.attachToTarget",
        "Runtime.enable", "Runtime.evaluate"].includes(method))
        throw Error("W11_NOT_ALLOWED_CDP_METHOD");
      if (closed) return Promise.reject(Error("W11_PIPE_CLOSED"));
      if (pending.size > 12) return Promise.reject(Error("W11_TOO_MANY_PENDING"));
      if (!Number.isInteger(timeoutMs) || timeoutMs < 100 || timeoutMs > 95000)
        throw Error("W11_UNSAFE_TIMEOUT");
      const id = ++nextId;
      const frame = Buffer.from(JSON.stringify({
        id, method, params, ...(sessionId ? { sessionId } : {})
      }) + "\0");
      if (frame.length > 32768) throw Error("W11_UNSAFE_COMMAND_SIZE");
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          pending.delete(id);
          reject(Error("W11_CDP_TIMEOUT_" + method));
        }, timeoutMs);
        pending.set(id, { resolve, reject, timer, sessionId });
        writer.write(frame, error => {
          if (error && pending.has(id)) {
            clearTimeout(timer);
            pending.delete(id);
            reject(Error("W11_CDP_WRITE_FAILED"));
          }
        });
      });
    },
    close() { rejectPending("W11_PIPE_CLOSED"); },
    stats() { return { closed, inflight: pending.size }; }
  });
}

export function exactFixtureTarget(target, origin, nonce) {
  if (!/^[a-f0-9]{32}$/.test(nonce || "")) return false;
  let t, expected;
  try { t = new URL(target?.url); expected = new URL(origin); }
  catch { return false; }
  return target.type === "page" &&
    target.title === "CELIKOM W7 isolated attach" &&
    expected.protocol === "http:" && expected.hostname === "127.0.0.1" &&
    Boolean(expected.port) && expected.pathname === "/" && !expected.search &&
    t.origin === expected.origin && t.pathname === "/" &&
    t.search === "?nonce=" + nonce && !t.hash;
}

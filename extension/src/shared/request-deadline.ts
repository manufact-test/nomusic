// A browser message can remain pending after its originating popup disappears.
// Bound the caller's wait without retrying writes or trusting a late response.
export function withDeadline<T>(operation: () => Promise<T>, timeoutMs = 30000): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("request_timeout")), timeoutMs);
    timer?.unref?.();
    try { Promise.resolve(operation()).then(resolve, reject).finally(() => clearTimeout(timer)); }
    catch (error) { clearTimeout(timer); reject(error); }
  });
}

// Bounded recovery for idempotent reads; never replay a write or trust online hints.
export function createReadRecovery() {
  let epoch = 0;
  const active = new Map();
  function reset() {
    epoch++;
    for (const [controller, method] of active) if (method === "GET") controller.abort("network_changed");
  }
  async function run(operation, method = "GET") {
    const generation = epoch;
    const deadline = Date.now() + 20000;
    for (let attempt = 0; ; attempt++) {
      if (method === "GET" && generation !== epoch) throw new Error("network_changed");
      const remaining = deadline - Date.now();
      if (remaining <= 0) throw new Error("request_timeout");
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), remaining);
      active.set(controller, method);
      let failed;
      try {
        const value = await operation(controller.signal);
        if (method === "GET" && generation !== epoch) throw new Error("network_changed");
        return value;
      } catch (error) {
        failed = error;
      } finally {
        clearTimeout(timer);
        active.delete(controller);
      }
      if (method !== "GET" || generation !== epoch || !failed?.retryable || attempt >= 2
        || deadline - Date.now() <= 1000) throw failed;
      await new Promise(resolve => setTimeout(resolve, attempt === 0 ? 500 : 1000));
    }
  }
  return { run, reset };
}

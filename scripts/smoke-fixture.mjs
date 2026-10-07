import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const port = 4174;
const child = spawn(process.execPath, [path.join(projectRoot, "scripts", "serve-fixture.mjs")], {
  cwd: projectRoot,
  env: { ...process.env, CELIKOM_FIXTURE_PORT: String(port) },
  stdio: ["ignore", "pipe", "pipe"]
});

let stderr = "";
child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });

async function waitForServer() {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/album/1/track/424242`);
      if (response.ok) return response;
    } catch (_error) {
      // The next bounded attempt handles normal process startup latency.
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error(`Fixture server did not start. ${stderr}`);
}

try {
  const htmlResponse = await waitForServer();
  const html = await htmlResponse.text();
  if (!html.includes("/album/1/track/424242") || !html.includes("original-player")) {
    throw new Error("Fixture HTML does not contain the expected Track ID and player");
  }

  const audioResponse = await fetch(`http://127.0.0.1:${port}/original-audio.mp3`);
  const audio = await audioResponse.arrayBuffer();
  if (!audioResponse.ok || audio.byteLength < 1024 || !String(audioResponse.headers.get("content-type")).startsWith("audio/mpeg")) {
    throw new Error("Fixture audio response is invalid");
  }
  console.log(`Fixture smoke test passed: ${audio.byteLength} audio bytes.`);
} finally {
  child.kill("SIGTERM");
}

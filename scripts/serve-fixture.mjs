import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const fixtureRoot = path.join(projectRoot, "spikes", "player-poc", "tests", "fixture");
const port = Number(process.env.CELIKOM_FIXTURE_PORT || 4173);

const server = http.createServer(async (request, response) => {
  try {
    if (request.url === "/original-audio.mp3") {
      const audio = await readFile(path.join(fixtureRoot, "original-audio.mp3"));
      response.writeHead(200, { "Content-Type": "audio/mpeg", "Content-Length": audio.length, "Cache-Control": "no-store" });
      response.end(audio);
      return;
    }
    const html = await readFile(path.join(fixtureRoot, "player-fixture.html"));
    response.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Content-Length": html.length, "Cache-Control": "no-store" });
    response.end(html);
  } catch (error) {
    response.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
    response.end(String(error?.message || error));
  }
});

server.listen(port, "127.0.0.1", () => {
  console.log(`CELIKOM fixture: http://localhost:${port}/album/1/track/424242`);
});

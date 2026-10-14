// Mirrors the server's conservative MPEG Layer III inspector; no decoding/upload.
export function mp3DurationMs(buffer): number | null {
  const data = new Uint8Array(buffer), size = data.length;
  if (size < 1024 || size > 31457280) return null;
  const marker = (offset, text) => [...text].every((char, i) => data[offset + i] === char.charCodeAt(0));
  let position = 0;
  if (marker(0, "ID3")) {
    const version = data[3], flags = data[5];
    if (![2, 3, 4].includes(version) || data[4] === 255 || (flags & (version === 2 ? 0x3f : version === 3 ? 0x1f : 0x0f)) || data.slice(6, 10).some(byte => byte & 128)) return null;
    position = 10 + (data[6] << 21) + (data[7] << 14) + (data[8] << 7) + data[9] + (version === 4 && flags & 16 ? 10 : 0);
  }
  if (position >= size - 1024) return null;
  let frames = 0, samples = 0, sampleRate = 0, mpegVersion = -1;
  const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
  while (position + 4 <= size) {
    const header = view.getUint32(position);
    if ((header >>> 21) !== 0x7ff) break;
    const version = (header >>> 19) & 3, layer = (header >>> 17) & 3, index = (header >>> 12) & 15, rateIndex = (header >>> 10) & 3;
    if (version === 1 || layer !== 1 || index < 1 || index > 14 || rateIndex === 3) break;
    const bitrate = (version === 3 ? [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320] : [0,8,16,24,32,40,48,56,64,80,96,112,128,144])[index];
    const rate = [44100,48000,32000][rateIndex] / (version === 3 ? 1 : version === 2 ? 2 : 4);
    const bytes = Math.floor((version === 3 ? 144 : 72) * bitrate * 1000 / rate) + ((header >>> 9) & 1);
    if (bytes < 24 || bytes > 1441 || position + bytes > size || (sampleRate && (sampleRate !== rate || mpegVersion !== version))) return null;
    sampleRate = rate; mpegVersion = version; samples += version === 3 ? 1152 : 576; position += bytes;
    if (++frames > 500000 || samples / sampleRate > 86400) return null;
  }
  if (size - position >= 128 && marker(position, "TAG")) position += 128;
  if (size - position > 4096 || frames < 2 || !sampleRate) return null;
  for (; position < size; position++) if (data[position] !== 0) return null;
  const ms = Math.round(1000 * samples / sampleRate);
  return ms >= 1000 && ms <= 86400000 ? ms : null;
}

export function durationNotice(originalMs, audioMs) {
  if (!Number.isFinite(originalMs) || !Number.isFinite(audioMs)) return { kind: "warning", text: "Не удалось сравнить длительность MP3. Файл дополнительно проверит сервер." };
  const delta = audioMs - originalMs, difference = Math.abs(delta);
  const time = ms => { const seconds=Math.round(ms/1000);return `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,"0")}`; };
  const description = `Оригинал: ${time(originalMs)} · файл: ${time(audioMs)}.`;
  if (difference <= 1500) return { kind: "ok", text: description + " Длительность подходит для подмены." };
  const mismatch = ` Файл ${delta > 0 ? "длиннее" : "короче"} на ${Math.round(difference / 1000)} с.`;
  return { blocked: true, kind: "error", text: description + mismatch + (difference > 5000 ? " Разница больше 5 секунд: выберите подходящую версию." : "") + " Допуск подмены — 1,5 с; с этим файлом подмена не запустится. Выберите файл подходящей длительности." };
}

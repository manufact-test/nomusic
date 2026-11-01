// Mirrors the server's conservative MPEG Layer III inspector; no decoding/upload.
export function mp3DurationMs(buffer): number | null {
  const data = new Uint8Array(buffer), size = data.length;
  if (size < 1024 || size > 31457280) return null;
  const marker = (offset, text) => [...text].every((char, i) => data[offset + i] === char.charCodeAt(0));
  // Downloaded/transcoded files may contain multiple consecutive ID3v2
  // headers (the reported user file contains two valid ID3v2.4 blocks).
  // Limit count/total metadata bytes, validate every synchsafe size and
  // inspect *all* MPEG frames after metadata. Never skip arbitrary bytes.
  let position = 0, leadingTags = 0;
  while (position + 10 <= size && marker(position, "ID3")) {
    if (++leadingTags > 4) return null;
    const version = data[position + 3], revision = data[position + 4], flags = data[position + 5];
    if (![2, 3, 4].includes(version) || revision === 255 ||
        (flags & (version === 2 ? 0x3f : version === 3 ? 0x1f : 0x0f)) ||
        data.slice(position + 6, position + 10).some(byte => byte & 128)) return null;
    const tagSize = (data[position + 6] << 21) + (data[position + 7] << 14)
      + (data[position + 8] << 7) + data[position + 9];
    const next = position + 10 + tagSize + (version === 4 && (flags & 16) ? 10 : 0);
    if (next > size - 1024 || next > 8 * 1024 * 1024 || next <= position) return null;
    position = next;
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
  // Accept bounded standard ID3v1 and APEv2 metadata trailers, which some
  // MP3 downloads append after the final complete MPEG frame.
  let tailEnd = size;
  if (tailEnd - position >= 128 && marker(tailEnd - 128, "TAG")) tailEnd -= 128;
  if (tailEnd - position >= 32 && marker(tailEnd - 32, "APETAGEX")) {
    const start = tailEnd - 32;
    const version = view.getUint32(start + 8, true);
    const bytes = view.getUint32(start + 12, true);
    const items = view.getUint32(start + 16, true);
    if (version !== 2000 || bytes < 32 || bytes > 1048576 || items > 128 ||
        bytes > tailEnd - position) return null;
    tailEnd -= bytes;
    // APEv2 may have a matching 32-byte header outside its size field.
    if (tailEnd - position >= 32 && marker(tailEnd - 32, "APETAGEX")) {
      if (view.getUint32(tailEnd - 24, true) !== version ||
          view.getUint32(tailEnd - 20, true) !== bytes) return null;
      tailEnd -= 32;
    }
  }
  if (tailEnd - position >= 128 && marker(tailEnd - 128, "TAG")) tailEnd -= 128;
  if (tailEnd - position >= 128 && marker(position, "TAG")) position += 128;
  if (tailEnd - position > 4096 || tailEnd < position || frames < 2 || !sampleRate) return null;
  for (; position < tailEnd; position++) if (data[position] !== 0) return null;
  const ms = Math.round(1000 * samples / sampleRate);
  return ms >= 1000 && ms <= 86400000 ? ms : null;
}

export function durationNotice(originalMs, audioMs) {
  if (!Number.isFinite(originalMs) || !Number.isFinite(audioMs)) return { blocked: true, kind: "error", text: "Не удалось прочитать аудиофайл и проверить его длительность. Проверьте, что это настоящий MP3 или M4A (AAC), либо выберите другой файл. Непроверенный файл не отправляется." };
  const delta = audioMs - originalMs, difference = Math.abs(delta);
  const time = ms => { const seconds=Math.floor(ms/1000);return `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,"0")}`; };
  const description = `Оригинал: ${time(originalMs)} · файл: ${time(audioMs)}.`;
  if (difference <= 1500) return { kind: "ok", text: description + " Длительность подходит для подмены." };
  const mismatch = ` Файл ${delta > 0 ? "длиннее" : "короче"} на ${Math.round(difference / 1000)} с.`;
  return { blocked: true, kind: "error", text: description + mismatch + (difference > 5000 ? " Разница больше 5 секунд: выберите подходящую версию." : "") + " Допуск подмены — 1,5 с; с этим файлом подмена не запустится. Выберите файл подходящей длительности." };
}

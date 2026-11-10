using System.Buffers.Binary;
using System.Globalization;
using System.Text;

namespace Celikom.Companion;

/// <summary>
/// Local upload preflight mirrored from extension/src/upload/mp3-duration.ts,
/// m4a.ts and the extension's strict 1500ms durationNotice contract.
/// No network, decoding, playback, or original Yandex file mutation.
/// </summary>
public static class AudioPreflight
{
    public const long MaxBytes = 31_457_280;
    public const long AllowedDeltaMs = 1_500;
    public sealed record Result(long? DurationMs, bool Blocked, string DurationMessage);

    public static async Task<Result> CheckAsync(string path, long? originalDurationMs,
        CancellationToken ct = default)
    {
        var info = new FileInfo(path);
        if (!info.Exists || info.Length is < 1024 or > MaxBytes ||
            !new[] { ".mp3", ".m4a" }.Contains(info.Extension,
                StringComparer.OrdinalIgnoreCase))
            return new Result(null, true, "Выберите MP3 или M4A размером до 30 МиБ.");
        byte[] bytes;
        try { bytes = await File.ReadAllBytesAsync(info.FullName, ct).ConfigureAwait(false); }
        catch (OperationCanceledException) { throw; }
        catch { return new Result(null, true, "Не удалось прочитать файл."); }
        long? duration;
        try
        {
            duration = info.Extension.Equals(".m4a", StringComparison.OrdinalIgnoreCase)
                ? M4aDurationMs(bytes) : Mp3DurationMs(bytes);
        }
        catch { duration = null; }

        if (duration is null)
            return new Result(null, true,
                "Не удалось проверить длительность аудиофайла. Этот файл нельзя отправить.");
        if (originalDurationMs is null or < 1000 or > 86400000)
            return new Result(duration, true,
                "Не удалось определить длительность текущей песни в Яндексе. Подождите определения трека.");
        var diff = Math.Abs(duration.Value - originalDurationMs.Value);
        var description = "Оригинал: " + Display(originalDurationMs.Value) +
            " · файл: " + Display(duration.Value) + ".";
        if (diff <= AllowedDeltaMs)
            return new Result(duration, false,
                description + " Длительность подходит для подмены.");
        var extra = diff > 5_000
            ? " Разница больше 5 секунд: выберите подходящую версию." : "";
        return new Result(duration, true,
            description + " Файл " +
            (duration.Value > originalDurationMs.Value ? "длиннее" : "короче") +
            " на " + Math.Round(diff / 1_000d, MidpointRounding.AwayFromZero)
                .ToString("0", CultureInfo.InvariantCulture) +
            " с." + extra +
            " Допуск подмены — 1,5 с. Выберите файл подходящей длительности.");
    }

    private static string Display(long ms)
    {
        var seconds = ms / 1000;
        return (seconds / 60).ToString(CultureInfo.InvariantCulture) + ":" +
            (seconds % 60).ToString("00", CultureInfo.InvariantCulture);
    }

    public static long? Mp3DurationMs(byte[] bytes)
    {
        var size = bytes.Length;
        if (size < 1024 || size > MaxBytes) return null;
        bool Marker(int at, string text)
        {
            if (at < 0 || at + text.Length > size) return false;
            for (var j = 0; j < text.Length; j++)
                if (bytes[at + j] != text[j]) return false;
            return true;
        }
        uint U32(int p, bool little = false) =>
            little ? BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(p, 4)) :
                BinaryPrimitives.ReadUInt32BigEndian(bytes.AsSpan(p, 4));
        int pos = 0, tags = 0;
        while (pos + 10 <= size && Marker(pos, "ID3"))
        {
            if (++tags > 4) return null;
            var ver = bytes[pos + 3];
            var rev = bytes[pos + 4];
            var flags = bytes[pos + 5];
            if (ver is not (2 or 3 or 4) || rev == 255 ||
                (flags & (ver == 2 ? 0x3f : ver == 3 ? 0x1f : 0x0f)) != 0)
                return null;
            for (var j = 6; j < 10; j++)
                if ((bytes[pos + j] & 128) != 0) return null;
            var tagSize = (bytes[pos + 6] << 21) + (bytes[pos + 7] << 14) +
                (bytes[pos + 8] << 7) + bytes[pos + 9];
            var next = pos + 10 + tagSize + (ver == 4 && (flags & 16) != 0 ? 10 : 0);
            if (next > size - 1024 || next > 8 * 1024 * 1024 || next <= pos) return null;
            pos = next;
        }
        if (pos >= size - 1024) return null;
        int frames = 0, sampleRate = 0, mpegVersion = -1;
        long samples = 0;
        while (pos + 4 <= size)
        {
            var h = U32(pos);
            if ((h >> 21) != 0x7ff) break;
            var ver = (int)((h >> 19) & 3);
            var layer = (int)((h >> 17) & 3);
            var idx = (int)((h >> 12) & 15);
            var rateIdx = (int)((h >> 10) & 3);
            if (ver == 1 || layer != 1 || idx is < 1 or > 14 || rateIdx == 3) break;
            int[] bits = ver == 3
                ? [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320]
                : [0,8,16,24,32,40,48,56,64,80,96,112,128,144];
            var rate = (new[] { 44100, 48000, 32000 })[rateIdx] /
                (ver == 3 ? 1 : ver == 2 ? 2 : 4);
            var frameLength = (int)Math.Floor((ver == 3 ? 144d : 72d) *
                bits[idx] * 1000 / rate) + (int)((h >> 9) & 1);
            if (frameLength is < 24 or > 1441 || pos + frameLength > size ||
                (sampleRate != 0 && (sampleRate != rate || mpegVersion != ver)))
                return null;
            sampleRate = rate;
            mpegVersion = ver;
            samples += ver == 3 ? 1152 : 576;
            pos += frameLength;
            if (++frames > 500000 || samples / sampleRate > 86400) return null;
        }
        var end = size;
        if (end - pos >= 128 && Marker(end - 128, "TAG")) end -= 128;
        if (end - pos >= 32 && Marker(end - 32, "APETAGEX"))
        {
            var tail = end - 32;
            var ver = U32(tail + 8, true);
            var length = U32(tail + 12, true);
            var items = U32(tail + 16, true);
            if (ver != 2000 || length < 32 || length > 1048576 ||
                items > 128 || length > end - pos) return null;
            end -= (int)length;
            if (end - pos >= 32 && Marker(end - 32, "APETAGEX"))
            {
                if (U32(end - 24, true) != ver || U32(end - 20, true) != length)
                    return null;
                end -= 32;
            }
        }
        if (end - pos >= 128 && Marker(end - 128, "TAG")) end -= 128;
        if (end - pos >= 128 && Marker(pos, "TAG")) pos += 128;
        if (end - pos > 4096 || end < pos || frames < 2 || sampleRate == 0) return null;
        for (var i = pos; i < end; i++)
            if (bytes[i] != 0) return null;
        var ms = (long)Math.Round(1000d * samples / sampleRate);
        return ms is >= 1000 and <= 86400000 ? ms : null;
    }

    private readonly record struct Box(string Type, int Start, int End);

    public static long? M4aDurationMs(byte[] bytes)
    {
        if (bytes.Length < 1024 || bytes.Length > MaxBytes) return null;
        var size = bytes.Length;
        uint U32(int p) => BinaryPrimitives.ReadUInt32BigEndian(bytes.AsSpan(p, 4));
        ushort U16(int p) => BinaryPrimitives.ReadUInt16BigEndian(bytes.AsSpan(p, 2));
        string FourCC(int p) => Encoding.ASCII.GetString(bytes, p, 4);
        var count = 0;
        List<Box> Boxes(int start, int end)
        {
            var list = new List<Box>();
            for (var p = start; p < end;)
            {
                if (++count > 8192 || end - p < 8) throw new InvalidDataException();
                var n = (long)U32(p);
                var head = 8;
                var type = FourCC(p + 4);
                if (n == 1)
                {
                    if (end - p < 16 || U32(p + 8) != 0) throw new InvalidDataException();
                    n = U32(p + 12);
                    head = 16;
                }
                if (n == 0) n = end - p;
                if (n < head || n > end - p) throw new InvalidDataException();
                list.Add(new Box(type, p + head, p + (int)n));
                p += (int)n;
            }
            return list;
        }
        Box One(List<Box> list, string type)
        {
            var a = list.Where(x => x.Type == type).ToArray();
            if (a.Length != 1) throw new InvalidDataException();
            return a[0];
        }
        var top = Boxes(0, size);
        if (top.Count == 0 || top[0].Type != "ftyp" ||
            top.Any(x => x.Type == "moof")) return null;
        var moov = One(top, "moov");
        var mdat = One(top, "mdat");
        if (mdat.End - mdat.Start < 512) return null;
        var tracks = Boxes(moov.Start, moov.End).Where(x => x.Type == "trak").ToArray();
        if (tracks.Length != 1) return null;
        var mdia = One(Boxes(tracks[0].Start, tracks[0].End), "mdia");
        var mdiaBoxes = Boxes(mdia.Start, mdia.End);
        var handler = One(mdiaBoxes, "hdlr");
        var header = One(mdiaBoxes, "mdhd");
        if (handler.End - handler.Start < 12 ||
            FourCC(handler.Start + 8) != "soun") return null;
        uint rate;
        ulong duration;
        var version = bytes[header.Start];
        if (version == 0 && header.End - header.Start >= 24)
        {
            rate = U32(header.Start + 12);
            duration = U32(header.Start + 16);
        }
        else if (version == 1 && header.End - header.Start >= 36 &&
            U32(header.Start + 24) == 0)
        {
            rate = U32(header.Start + 20);
            duration = U32(header.Start + 28);
        }
        else return null;
        if (rate == 0 || duration == 0) return null;
        var seconds = duration / (double)rate;
        if (seconds is < 1 or > 86400) return null;
        var minf = One(mdiaBoxes, "minf");
        var stbl = One(Boxes(minf.Start, minf.End), "stbl");
        var tables = Boxes(stbl.Start, stbl.End);
        var stsd = One(tables, "stsd");
        var stsz = One(tables, "stsz");
        var stts = One(tables, "stts");
        if (stsd.End - stsd.Start < 8 || U32(stsd.Start + 4) != 1) return null;
        var entry = One(Boxes(stsd.Start + 8, stsd.End), "mp4a");
        if (entry.End - entry.Start < 28 || U16(entry.Start + 8) != 0) return null;
        var channels = U16(entry.Start + 16);
        var sampleRate = U32(entry.Start + 24) >> 16;
        if (channels is < 1 or > 2 || sampleRate is < 8000 or > 48000)
            return null;
        var extra = Boxes(entry.Start + 28, entry.End);
        if (extra.Any(b => b.Type is "sinf" or "schm") ||
            !extra.Any(b => b.Type == "esds")) return null;
        if (stsz.End - stsz.Start < 12 || stts.End - stts.Start < 8) return null;
        var samples = U32(stsz.Start + 8);
        var entries = U32(stts.Start + 4);
        if (samples == 0 || samples > 500000 || entries > samples ||
            stts.End - stts.Start != 8 + entries * 8) return null;
        ulong sampleCount = 0, totalTime = 0;
        for (var i = 0; i < entries; i++)
        {
            var n = U32(stts.Start + 8 + (int)i * 8);
            var delta = U32(stts.Start + 12 + (int)i * 8);
            if (n == 0 || delta == 0) return null;
            sampleCount += n;
            totalTime += (ulong)n * delta;
        }
        if (sampleCount != samples ||
            Math.Abs((double)totalTime - duration) > rate / 10d) return null;
        return (long)Math.Round(seconds * 1000d);
    }
}

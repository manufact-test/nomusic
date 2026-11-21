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
                info.Extension.Equals(".mp3", StringComparison.OrdinalIgnoreCase)
                    ? "MP3 повреждён или содержит неподдерживаемые данные. Служебные теги очищаются автоматически; выберите другой исходный файл."
                    : "Не удалось проверить длительность M4A. Выберите другой файл AAC без DRM.");
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
            for (var i = 0; i < text.Length; i++)
                if (bytes[at + i] != text[i]) return false;
            return true;
        }
        bool AllZero(int from, int to)
        {
            if (from < 0 || to < from || to > size) return false;
            for (var i = from; i < to; i++)
                if (bytes[i] != 0) return false;
            return true;
        }
        uint U32(int at, bool little = false) =>
            little ? BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(at, 4)) :
                BinaryPrimitives.ReadUInt32BigEndian(bytes.AsSpan(at, 4));

        var position = 0;
        var tagCount = 0;
        var metadataBytes = 0;
        bool SkipLeadingTags()
        {
            while (Marker(position, "ID3"))
            {
                if (position + 10 > size || ++tagCount > 4) return false;
                var version = bytes[position + 3];
                var revision = bytes[position + 4];
                var flags = bytes[position + 5];
                if (version is not (2 or 3 or 4) || revision == 255 ||
                    (flags & (version == 2 ? 0x3f : version == 3 ? 0x1f : 0x0f)) != 0)
                    return false;
                for (var i = 6; i < 10; i++)
                    if ((bytes[position + i] & 128) != 0) return false;
                var length = 10 + (bytes[position + 6] << 21) +
                    (bytes[position + 7] << 14) + (bytes[position + 8] << 7) +
                    bytes[position + 9] +
                    (version == 4 && (flags & 16) != 0 ? 10 : 0);
                metadataBytes += length;
                if (position + length > size || metadataBytes > 8 * 1024 * 1024)
                    return false;
                if (version == 4 && (flags & 16) != 0 &&
                    !Marker(position + length - 10, "3DI")) return false;
                position += length;
            }
            return true;
        }

        (int Bytes, int Rate, int Version, int Samples, bool Metadata)? FrameAt(int at)
        {
            if (at + 4 > size) return null;
            var header = U32(at);
            var version = (int)((header >> 19) & 3);
            var layer = (int)((header >> 17) & 3);
            var bitrateIndex = (int)((header >> 12) & 15);
            var rateIndex = (int)((header >> 10) & 3);
            if ((header >> 21) != 0x7ff || version == 1 || layer != 1 ||
                bitrateIndex is < 1 or > 14 || rateIndex == 3) return null;

            int[] bitrates = version == 3
                ? [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
                : [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144];
            var rate = new[] { 44100, 48000, 32000 }[rateIndex] /
                (version == 3 ? 1 : version == 2 ? 2 : 4);
            var frameBytes = (int)Math.Floor((version == 3 ? 144d : 72d) *
                bitrates[bitrateIndex] * 1000 / rate) + (int)((header >> 9) & 1);
            if (frameBytes is < 24 or > 1441 || at + frameBytes > size) return null;

            var crcBytes = ((header >> 16) & 1) == 0 ? 2 : 0;
            var mono = ((header >> 6) & 3) == 3;
            var sideInfoBytes = version == 3
                ? (mono ? 17 : 32) : (mono ? 9 : 17);
            var sideInfoStart = at + 4 + crcBytes;
            var infoAt = sideInfoStart + sideInfoBytes;
            var metadata = (Marker(infoAt, "Info") || Marker(infoAt, "Xing")) &&
                infoAt + 8 <= at + frameBytes && AllZero(sideInfoStart, infoAt);
            return (frameBytes, rate, version, version == 3 ? 1152 : 576, metadata);
        }

        if (!SkipLeadingTags()) return null;

        (int Bytes, int Rate, int Version, int Samples, bool Metadata)? signature = null;
        var hasFirstInfo = false;
        var metadataFrames = 0;
        while (true)
        {
            var frame = FrameAt(position);
            if (frame is null || !frame.Value.Metadata) break;
            if (++metadataFrames > 4) return null;
            var current = frame.Value;
            if (signature is not null &&
                (signature.Value.Rate != current.Rate ||
                 signature.Value.Version != current.Version)) return null;
            signature ??= current;
            hasFirstInfo = true;
            position += current.Bytes;
            if (!SkipLeadingTags()) return null;
        }

        var audioFrames = 0;
        long samples = hasFirstInfo ? signature!.Value.Samples : 0;
        var sampleRate = signature?.Rate ?? 0;
        var mpegVersion = signature?.Version ?? -1;
        while (position + 4 <= size)
        {
            var frame = FrameAt(position);
            if (frame is null) break;
            var current = frame.Value;
            if (current.Metadata ||
                (sampleRate != 0 &&
                 (sampleRate != current.Rate || mpegVersion != current.Version)))
                return null;
            sampleRate = current.Rate;
            mpegVersion = current.Version;
            position += current.Bytes;
            samples += current.Samples;
            if (++audioFrames > 500000 || samples / (double)sampleRate > 86400) return null;
        }

        var audioEnd = position;
        var end = size;
        if (end - position >= 128 && Marker(end - 128, "TAG")) end -= 128;
        if (end - position >= 32 && Marker(end - 32, "APETAGEX"))
        {
            var footer = end - 32;
            var apeVersion = U32(footer + 8, little: true);
            var apeBytes = U32(footer + 12, little: true);
            var itemCount = U32(footer + 16, little: true);
            if (apeVersion != 2000 || apeBytes < 32 || apeBytes > 1_048_576 ||
                itemCount > 128 || apeBytes > end - position) return null;
            end -= (int)apeBytes;
            if (end - position >= 32 && Marker(end - 32, "APETAGEX"))
            {
                if (U32(end - 24, little: true) != apeVersion ||
                    U32(end - 20, little: true) != apeBytes) return null;
                end -= 32;
            }
        }
        if (end - position >= 128 && Marker(end - 128, "TAG")) end -= 128;
        if (end - position >= 128 && Marker(position, "TAG"))
        {
            var tailLength = end - position;
            if (tailLength == 128 || AllZero(position + 128, end))
            {
                position = end;
            }
            else
            {
                if (tailLength > 512) return null;
                string text;
                try
                {
                    text = new UTF8Encoding(false, true).GetString(
                        bytes, position + 3, tailLength - 4);
                }
                catch (DecoderFallbackException) { return null; }
                var characters = 0;
                foreach (var rune in text.EnumerateRunes())
                {
                    if (Rune.IsControl(rune)) return null;
                    characters++;
                }
                if (characters != 124) return null;
                position = end;
            }
        }

        if (end < position || end - position > 4096 ||
            !AllZero(position, end) || audioFrames < 2 || sampleRate == 0)
            return null;
        var durationMs = (long)Math.Round(
            1000d * samples / sampleRate, MidpointRounding.AwayFromZero);
        return durationMs is >= 1000 and <= 86400000 ? durationMs : null;
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

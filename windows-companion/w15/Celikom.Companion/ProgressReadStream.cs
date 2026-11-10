namespace Celikom.Companion;

/// <summary>
/// Counts bytes read by HttpClient's multipart serializer, not fabricated
/// server-side progress. Never buffers the entire user's audio in memory.
/// </summary>
public sealed class ProgressReadStream : Stream
{
    private readonly Stream _source;
    private readonly IProgress<int> _progress;
    private long _read;
    private int _lastPercent = -1;

    public ProgressReadStream(Stream source, IProgress<int> progress)
    {
        _source = source ?? throw new ArgumentNullException(nameof(source));
        _progress = progress ?? throw new ArgumentNullException(nameof(progress));
        if (!_source.CanRead || !_source.CanSeek || _source.Length <= 0)
            throw new ArgumentException("Readable seekable source required", nameof(source));
    }

    private void Advance(int count)
    {
        if (count <= 0) return;
        _read += count;
        var percent = (int)Math.Clamp(_read * 100 / _source.Length, 0, 100);
        if (percent <= _lastPercent) return;
        _lastPercent = percent;
        _progress.Report(percent);
    }

    public override bool CanRead => _source.CanRead;
    public override bool CanSeek => _source.CanSeek;
    public override bool CanWrite => false;
    public override long Length => _source.Length;
    public override long Position { get => _source.Position; set => _source.Position = value; }
    public override void Flush() => _source.Flush();
    public override long Seek(long offset, SeekOrigin origin) => _source.Seek(offset, origin);
    public override int Read(byte[] buffer, int offset, int count)
    {
        var n = _source.Read(buffer, offset, count);
        Advance(n);
        return n;
    }
    public override int Read(Span<byte> buffer)
    {
        var n = _source.Read(buffer);
        Advance(n);
        return n;
    }
    public override async ValueTask<int> ReadAsync(Memory<byte> buffer,
        CancellationToken cancellationToken = default)
    {
        var n = await _source.ReadAsync(buffer, cancellationToken).ConfigureAwait(false);
        Advance(n);
        return n;
    }
    public override async Task<int> ReadAsync(byte[] buffer, int offset, int count,
        CancellationToken cancellationToken)
    {
        var n = await _source.ReadAsync(buffer, offset, count, cancellationToken)
            .ConfigureAwait(false);
        Advance(n);
        return n;
    }
    public override void SetLength(long value) => throw new NotSupportedException();
    public override void Write(byte[] buffer, int offset, int count) =>
        throw new NotSupportedException();
    protected override void Dispose(bool disposing)
    {
        if (disposing) _source.Dispose();
        base.Dispose(disposing);
    }
}

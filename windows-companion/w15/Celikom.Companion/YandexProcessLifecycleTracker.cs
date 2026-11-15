namespace Celikom.Companion;

public sealed class YandexProcessLifecycleTracker
{
    private bool _observedRunning;

    public bool Observe(bool running)
    {
        if (running)
        {
            _observedRunning = true;
            return false;
        }
        if (!_observedRunning) return false;
        _observedRunning = false;
        return true;
    }
}

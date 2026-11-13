using System.Text.Json;

namespace Celikom.Companion;

/// <summary>
/// Only auth/activate is safe for one bounded retry. The actual server trial
/// activation is idempotent (one locked account_trials row per user). Never
/// apply this to support messages, uploads, promos or arbitrary POSTs.
/// </summary>
public static class StartupActivationRecovery
{
    public static async Task<JsonElement> ActivateAsync(
        Func<CancellationToken, Task<JsonElement>> activate,
        Func<bool> stillSameStart,
        Action<string>? record = null,
        CancellationToken cancellationToken = default)
    {
        try
        {
            return await activate(cancellationToken);
        }
        catch (Exception error) when (SafeToRetry(error) &&
            stillSameStart() && !cancellationToken.IsCancellationRequested)
        {
            record?.Invoke(EntitlementCheckRecovery.FailureCode(error));
            record?.Invoke("START_ENTITLEMENT_RETRY");
            await Task.Delay(450, cancellationToken);
            cancellationToken.ThrowIfCancellationRequested();
            if (!stillSameStart()) throw new OperationCanceledException();
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(7));
            var allowed = await activate(timeout.Token);
            record?.Invoke("START_ENTITLEMENT_RETRY_OK");
            return allowed;
        }
    }

    public static bool SafeToRetry(Exception error) =>
        EntitlementCheckRecovery.IsTransient(error) &&
        // An explicit throttle is not a transport glitch; re-POSTing would
        // only worsen it. 401/403 are already excluded by IsTransient.
        error is not ApiFailure { HttpStatus: 429 };
}

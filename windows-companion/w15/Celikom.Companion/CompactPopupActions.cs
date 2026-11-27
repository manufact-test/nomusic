using Celikom.NativeInstaller;
using System.Globalization;
using System.Text.Json;
using System.Windows.Forms;

namespace Celikom.Companion;

public sealed partial class MainWindow
{
    private Guid _compactSupportKey = Guid.NewGuid();
    private CancellationTokenSource? _compactUploadCancellation;

    private static string JsonText(JsonElement element, string key)
    {
        if (element.ValueKind == JsonValueKind.Object &&
            element.TryGetProperty(key, out var value) && value.ValueKind == JsonValueKind.String)
            return value.GetString() ?? "";
        return "";
    }

    private static string AccessLabel(JsonElement access)
    {
        if (access.ValueKind != JsonValueKind.Object) return "Не удалось проверить доступ";
        var allowed = access.TryGetProperty("allowed", out var a) &&
            a.ValueKind == JsonValueKind.True;
        var source = JsonText(access, "source");
        var reason = JsonText(access, "reason");
        if (allowed && source == "promo" &&
            access.TryGetProperty("valid_until", out var until) &&
            until.ValueKind == JsonValueKind.Null)
            return "Промокод · доступ навсегда";
        if (allowed && access.TryGetProperty("valid_until", out var until2) &&
            until2.ValueKind == JsonValueKind.String &&
            DateTimeOffset.TryParse(until2.GetString(), CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal, out var expiration))
        {
            var target = expiration.ToOffset(TimeSpan.FromHours(3));
            var date = target.ToString("d MMMM, HH:mm", CultureInfo.GetCultureInfo("ru-RU"));
            var prefix = source == "promo" ? "Промокод до " :
                source == "subscription" ? "Подписка до " : "Пробный период до ";
            return prefix + date + " (Москва)";
        }
        if (reason == "trial_not_started") return "3 дня пробного периода начнутся после «Старт»";
        if (reason == "email_unverified") return "Подтверди почту, чтобы начать";
        if (reason == "service_incident") return "Сбой интеграции · доступ компенсируем";
        if (reason == "account_disabled") return "Доступ к аккаунту отключён";
        return source == "subscription" ? "Подписка завершена" : "Пробный период завершён";
    }

    private async Task RefreshCompactAccessAsync(bool force = false)
    {
        if (!_compactReady || _closing || !IsHandleCreated) return;
        if (!_api.IsLoggedIn)
        {
            _resumeAfterNetworkFailure = false;
            _bridge.SetNativeNetworkRecoveryPending(false);
            ++_compactAccessGeneration;
            ClearCompactAccessConfirmation();
            SetCompactAccessText("Войдите в аккаунт, чтобы начать");
            return;
        }
        if (_compactAccessBusy) return;
        if (!force && DateTimeOffset.UtcNow - _compactAccessChecked < TimeSpan.FromSeconds(75))
            return;
        var generation = ++_compactAccessGeneration;
        var account = _api.Settings;
        bool StillSameUser() => generation == _compactAccessGeneration && !_closing &&
            !IsDisposed && _api.IsLoggedIn &&
            _api.Settings.InstallationId == account.InstallationId &&
            string.Equals(_api.Settings.Email, account.Email, StringComparison.OrdinalIgnoreCase);
        _compactAccessBusy = true;
        using var requestCancellation = new CancellationTokenSource();
        _compactAccessRequestCancellation = requestCancellation;
        var fastRoute = EntitlementCheckRecovery.FastRouteCheck(
            _resumeAfterNetworkFailure, DateTimeOffset.UtcNow, _lastNetworkRecheckHint);
        if (fastRoute)
            requestCancellation.CancelAfter(EntitlementCheckRecovery.QuickRecheckTimeout);
        // Previously we replaced "Промокод · доступ навсегда" with "Проверяем
        // доступ…" on EVERY 15-second poll. That was the visible blinking.
        // Keep the confirmed label stable; server check and revoke still run.
        SetCompactAccessText(CompactAccessRefresh.WhileChecking(_compactAccess.Text,
            _compactAccessConfirmedInstallation, _compactAccessConfirmedEmail,
            account.InstallationId, account.Email));
        try
        {
            JsonElement response;
            try { response = await _api.GetEntitlementAsync(requestCancellation.Token); }
            catch (Exception ex) when (!fastRoute && _bridge.Enabled &&
                EntitlementCheckRecovery.IsTransient(ex))
            {
                // Keep the previous bounded retry during ordinary playback.
                // On a VPN change we instead cancel the stale request and run
                // a fresh short check; never queue old and new routes together.
                DiagnosticLog.Record("ACTIVE_ENTITLEMENT_RETRY");
                await Task.Delay(400, requestCancellation.Token);
                using var retryTimeout =
                    CancellationTokenSource.CreateLinkedTokenSource(requestCancellation.Token);
                retryTimeout.CancelAfter(TimeSpan.FromSeconds(3));
                response = await _api.GetEntitlementAsync(retryTimeout.Token);
                DiagnosticLog.Record("ACTIVE_ENTITLEMENT_RETRY_OK");
            }
            if (requestCancellation.IsCancellationRequested && _networkRouteRecheckPending)
                return;
            if (!StillSameUser()) return;
            // A fresh authenticated response closes the fast-route window.
            // Ordinary 15-second entitlement polling must not keep using the
            // short VPN timeout after connectivity has already recovered.
            _lastNetworkRecheckHint = DateTimeOffset.MinValue;
            _compactAccessConfirmedInstallation = account.InstallationId;
            _compactAccessConfirmedEmail = account.Email;
            SetCompactAccessText(AccessLabel(response));
            _compactAccessChecked = DateTimeOffset.UtcNow;
            var allowed = PlaybackEntitlement.Allowed(response, DateTimeOffset.UtcNow);
            if (!allowed)
            {
                _resumeAfterNetworkFailure = false; // authoritative deny NEVER reconnects
                _bridge.SetNativeNetworkRecoveryPending(false);
                if (_bridge.Enabled)
                {
                    ++_compactStartEpoch;
                    _compactStarting = false;
                    _bridge.SetEnabled(false);
                    DiagnosticLog.Record("ACTIVE_ENTITLEMENT_REVOKED");
                }
            }
            else if (EntitlementCheckRecovery.MayResume(
                _resumeAfterNetworkFailure, _api.IsLoggedIn,
                _nativeInstallState == NativeInstallState.Active,
                _installedModule.MatchesApplication, response, DateTimeOffset.UtcNow))
            {
                // This was automatically stopped only after a transient failure.
                // Restore ONLY after a brand-new signed-in server success; manual
                // Stop, logout, account change and expired access cancel recovery.
                var wasNetworkSuspended = _resumeAfterNetworkFailure;
                _resumeAfterNetworkFailure = false;
                _bridge.SetEnabled(true);
                // Keep the route marker until the resumed native player publishes
                // its first heartbeat. The host can preserve an already-live
                // signed decoder instead of forcing two consecutive source reloads.
                if (!wasNetworkSuspended)
                    _bridge.SetNativeNetworkRecoveryPending(false);
                DiagnosticLog.Record("ACTIVE_ENTITLEMENT_RECOVERED");
            }
            else
            {
                _resumeAfterNetworkFailure = false;
                _bridge.SetNativeNetworkRecoveryPending(false);
            }
        }
        catch (OperationCanceledException) when (
            requestCancellation.IsCancellationRequested && _networkRouteRecheckPending)
        {
            // Windows reported a new VPN route. A GET on the retired route
            // carries no new authority; scheduled fresh validation replaces it.
            DiagnosticLog.Record("ACTIVE_ENTITLEMENT_OLD_ROUTE_CANCELLED");
        }
        catch (Exception ex)
        {
            if (!StillSameUser()) return;
            DiagnosticLog.Record(EntitlementCheckRecovery.FailureCode(ex));
            var transient = EntitlementCheckRecovery.IsTransient(ex);
            if (_bridge.Enabled)
            {
                ++_compactStartEpoch;
                _compactStarting = false;
                _resumeAfterNetworkFailure = transient &&
                    _nativeInstallState == NativeInstallState.Active &&
                    _installedModule.MatchesApplication;
                if (_resumeAfterNetworkFailure && !_bridge.NativeNetworkRecoveryPending)
                    _networkRecoveryPlaybackState = _bridge.HasFreshHeartbeat
                        ? _bridge.LastPlaybackState : "UNKNOWN";
                _bridge.SetNativeNetworkRecoveryPending(_resumeAfterNetworkFailure);
                _bridge.SetEnabled(false); // fail closed until new live authority
                DiagnosticLog.Record(transient ?
                    "ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED" :
                    "ACTIVE_ENTITLEMENT_CHECK_UNAVAILABLE");
            }
            else if (!transient && _resumeAfterNetworkFailure)
            {
                _resumeAfterNetworkFailure = false;
                _bridge.SetNativeNetworkRecoveryPending(false);
                DiagnosticLog.Record("ACTIVE_ENTITLEMENT_RECOVERY_DENIED");
            }
            else if (!transient)
                _bridge.SetNativeNetworkRecoveryPending(false);
            else
                _bridge.SetNativeNetworkRecoveryPending(_resumeAfterNetworkFailure);
            SetCompactAccessText(_resumeAfterNetworkFailure
                ? CompactPlaybackPresentation.NetworkRecoveryMessage
                : "Доступ не подтверждён. Подмена выключена.");
        }
        finally
        {
            if (ReferenceEquals(_compactAccessRequestCancellation, requestCancellation))
                _compactAccessRequestCancellation = null;
            _compactAccessBusy = false;
            if (!_closing && !IsDisposed)
            {
                UpdateSafe();
                if (_networkRouteRecheckPending &&
                    (_bridge.Enabled || _resumeAfterNetworkFailure))
                    _ = RecheckAfterRouteSettledAsync(_networkRouteEpoch);
            }
        }
    }

    private bool IsCompactCurrentTrack(string trackId)
    {
        if (!GrantValidator.IsTrackId(trackId) || _compactHoldingTrackTransition)
            return false;
        var current = _bridge.GetPlaybackSnapshot();
        return string.Equals(current.TrackId, trackId, StringComparison.Ordinal);
    }

    private void EnsureCompactPresenceTrack(string trackId)
    {
        if (string.Equals(_compactPresenceTrack, trackId, StringComparison.Ordinal))
            return;
        _compactPresenceTrack = trackId;
        _compactPresenceStatus = _api.IsLoggedIn ? "checking" : "";
        _compactPresenceChecked = DateTimeOffset.MinValue;
        ++_compactPresenceEpoch;
    }

    // An authoritative mutation invalidates any older GET that may still be
    // in flight. Its epoch can no longer overwrite the newer local status.
    private bool SetCompactPresenceStatus(string trackId, string status)
    {
        if (!IsCompactCurrentTrack(trackId)) return false;
        EnsureCompactPresenceTrack(trackId);
        ++_compactPresenceEpoch;
        _compactPresenceStatus = status;
        _compactPresenceChecked = DateTimeOffset.UtcNow;
        return true;
    }

    private void CompactResult(bool upload, string trackId, string title, string note)
    {
        // Never let an old request paint a result over a newly selected song.
        if (!IsCompactCurrentTrack(trackId)) return;
        if (upload)
        {
            _compactUploadView = "result";
            _compactUploadResultTitle.Text = title;
            _compactUploadResultNote.Text = note;
            _compactUploadNote.Text = "";
        }
        else
        {
            _compactSuggestView = "result";
            _compactSuggestResultTitle.Text = title;
            _compactSuggestResultNote.Text = note;
            _compactSuggestNote.Text = "";
        }

        RenderCompact();
        LayoutCompact();
    }

    private async Task<string> ReadCompactPresenceAsync(string trackId, bool force)
    {
        if (!GrantValidator.IsTrackId(trackId) || !_api.IsLoggedIn)
            throw new ApiFailure(401, "not_logged_in");

        var requestEpoch = _compactPresenceEpoch;
        var now = DateTimeOffset.UtcNow;
        if (!force && string.Equals(_compactPresenceTrack, trackId, StringComparison.Ordinal) &&
            CompactPlaybackPresentation.PresenceCacheFresh(
                _compactPresenceStatus, _compactPresenceChecked, now))
            return _compactPresenceStatus;

        if (_compactPresencePending is { IsCompleted: false } &&
            string.Equals(_compactPresencePendingTrack, trackId, StringComparison.Ordinal) &&
            _compactPresencePendingEpoch == requestEpoch)
            return await _compactPresencePending;

        async Task<string> Read()
        {
            try
            {
                var response = await _api.GetTrackVersionStatusAsync(trackId);
                return JsonText(response, "status") switch
                {
                    "approved" => "approved",
                    "pending" => "pending",
                    _ => "none"
                };
            }
            catch
            {
                return "error";
            }
        }

        var task = Read();
        _compactPresencePending = task;
        _compactPresencePendingTrack = trackId;
        _compactPresencePendingEpoch = requestEpoch;
        try
        {
            var status = await task;
            if (CompactPlaybackPresentation.PresenceResponseMatchesCurrent(
                    _compactPresenceTrack, _compactPresenceEpoch, trackId, requestEpoch) &&
                IsCompactCurrentTrack(trackId) && _api.IsLoggedIn && !_closing)
            {
                _compactPresenceStatus = status;
                _compactPresenceChecked = DateTimeOffset.UtcNow;
                RenderCompact();
                LayoutCompact();
            }
            return status;
        }
        finally
        {
            if (ReferenceEquals(_compactPresencePending, task))
            {
                _compactPresencePending = null;
                _compactPresencePendingTrack = "";
                _compactPresencePendingEpoch = 0;
            }
        }
    }

    private async Task RefreshCompactPresenceAsync(string trackId)
    {
        var requestEpoch = _compactPresenceEpoch;
        try
        {
            await ReadCompactPresenceAsync(trackId, force: false);
        }
        catch
        {
            if (CompactPlaybackPresentation.PresenceResponseMatchesCurrent(
                    _compactPresenceTrack, _compactPresenceEpoch, trackId, requestEpoch) &&
                IsCompactCurrentTrack(trackId) && _api.IsLoggedIn && !_closing)
            {
                _compactPresenceStatus = "error";
                _compactPresenceChecked = DateTimeOffset.MinValue;
                RenderCompact();
                LayoutCompact();
            }
        }
    }

    private async Task OpenCompactContributionAsync(bool upload)
    {
        if (_compactContributionBusy) return;
        var generation = ++_compactOpenEpoch;
        if (upload)
        {
            _compactUploadOpen = true;
            _compactSuggestOpen = false;
            _compactUploadView = "checking";
            _compactUploadNote.Text = "Проверяем, есть ли версия этой песни…";
        }
        else
        {
            _compactSuggestOpen = true;
            _compactUploadOpen = false;
            _compactSuggestView = "checking";
            _compactSuggestNote.Text = "Проверяем, есть ли версия этой песни…";
        }
        LayoutCompact();
        ScrollCompactTo(upload ? _compactUploadButton : _compactSuggestButton);

        var playback = _bridge.GetPlaybackSnapshot();
        var id = playback.TrackId;
        try
        {
            if (!GrantValidator.IsTrackId(id))
                throw new ApiFailure(409,
                    playback.HeartbeatFresh && !playback.PlayerUnavailable
                        ? "TRACK_RESOLVING" : "TRACK_REQUIRED");
            if (!_api.IsLoggedIn)
                throw new ApiFailure(401, "not_logged_in");

            EnsureCompactPresenceTrack(id);
            // Reuse the fresh 15-second cache or an in-flight request. Opening
            // the same song window must not force another network round-trip.
            var status = await ReadCompactPresenceAsync(id, force: false);
            if (generation != _compactOpenEpoch || !IsCompactCurrentTrack(id) || !_api.IsLoggedIn)
                return;
            if (status == "approved")
                CompactResult(upload, id, "Версия уже доступна",
                    "Для этой песни уже есть одобренная версия CELIKOM. Повторная отправка не требуется.");
            else if (status == "pending")
                CompactResult(upload, id, upload ? "Трек уже добавлен" : "Версия уже на проверке",
                    "Альтернативная версия ожидает проверки. Повторная отправка не требуется.");
            else if (status == "error")
                CompactResult(upload, id, "Не удалось проверить статус",
                    "Не удалось получить состояние песни. Проверь интернет и повтори.");
            else if (upload)
            {
                _compactPinnedUploadTrack = id;
                _compactUploadView = "form";
                _compactUploadNote.Text = "";
                _compactUploadNote.ForeColor = Secondary;
                _compactFileName.Text = "";
                _compactSelectedAudio = null;
                _compactFilePicker.SelectedFile = "";
                _compactRights.Checked = false;
            }
            else
            {
                _compactPinnedSuggestTrack = id;
                _compactSuggestView = "form";
                _compactSuggestNote.Text = "";
            }
        }
        catch (Exception ex)
        {
            if (generation != _compactOpenEpoch) return;
            var message = ex is ApiFailure a && a.Category == "TRACK_REQUIRED"
                ? "Сначала запусти песню в Яндекс.Музыке."
                : ex is ApiFailure b && b.Category == "TRACK_RESOLVING"
                    ? "Яндекс подключён, но данные текущей песни ещё обновляются. Подожди немного."
                    : DescribeAccountError(ex);
            if (upload)
            {
                _compactUploadView = "error";
                _compactUploadNote.Text = message;
            }
            else
            {
                _compactSuggestView = "error";
                _compactSuggestNote.Text = message;
            }
        }
        finally
        {
            if (generation == _compactOpenEpoch)
            {
                RenderCompact();
                LayoutCompact();
                ScrollCompactTo(upload ? _compactUploadButton : _compactSuggestButton);
            }
        }
    }

    private static string DescribeAccountError(Exception ex)
    {
        if (ex is ApiFailure e) return e.Category switch
        {
            "INVALID_CREDENTIALS" => "Проверь email и пароль.",
            "EMAIL_VERIFICATION_REQUIRED" => "Подтверди почту кодом из письма.",
            "INVALID_SESSION" => "Сессия истекла. Войди повторно.",
            "RATE_LIMITED" => "Слишком много попыток. Попробуй позже.",
            "INVALID_CODE" or "invalid_code" => "Неверный или просроченный код.",
            "weak_password" => "Пароль: минимум 12 символов.",
            "invalid_promo" or "INVALID_PROMO" => "Проверь код промокода.",
            "promo_lifetime_active" => "Бессрочный доступ уже активирован.",
            "promo_payment_pending" => "Промокод станет доступен после подключения оплаты.",
            "promo_unavailable" => "Промокод недоступен или закончился.",
            "rate_limited" => "Слишком много попыток. Попробуй позже.",
            "track_pending" => "Эту песню уже проверяют.",
            "track_already_approved" => "У песни уже есть альтернативная версия.",
            "duration_mismatch" => "Длительность файла отличается от оригинала.",
            "rights_declaration_required" => "Сначала подтверди права на файл.",
            "invalid_mp3" => "MP3 повреждён или содержит неподдерживаемые данные. Служебные теги очищаются автоматически; выбери другой исходный файл.",
            "invalid_m4a" => "M4A не поддерживается или повреждён. Нужен M4A с кодеком AAC без защиты DRM.",
            "upload_too_large" => "Файл превышает допустимый размер 30 МиБ.",
            "TRACK_REQUIRED" => "Сначала запусти песню в Яндекс.Музыке.",
            "TRACK_RESOLVING" => "Яндекс подключён, но данные текущей песни ещё обновляются. Подожди немного.",
            "TRACK_CHANGED" => "Песня сменилась. Открой действие заново.",
            "UPLOAD_NOT_CONFIRMED" => "Сервер не подтвердил отправку. Проверь статус трека перед повторной загрузкой.",
            "INVALID_FILE" => "Выбери MP3 или M4A размером до 30 МиБ.",
            "INVALID_DURATION" => "Проверь длительность.",
            _ => "Не удалось выполнить действие. Проверь интернет и повтори."
        };
        return "Нет связи. Повтори попытку позже.";
    }

    private async void CompactAccountSubmitAsync(object? sender, EventArgs e)
    {
        if (_loggingIn) return;
        _loggingIn = true;
        _login.Enabled = false;
        var mode = _compactAccountMode;
        var email = _email.Text.Trim();
        var password = _password.Text;
        try
        {
            if (mode == "login")
            {
                ++_compactStartEpoch;
                _compactStarting = false;
                _resumeAfterNetworkFailure = false;
                ++_compactAccessGeneration;
                ClearCompactAccessConfirmation();
                _bridge.SetEnabled(false);
                await _api.LoginAsync(_origin.Text.Trim(), email, password);
                ResetCompactBenefits();
                _password.Clear();
                _compactAccountMessage.Text = "";
                _compactAccountOpen = false;
                _compactAccountMode = "login";
                await RefreshDiagnosticsAccessAsync();
                _compactAccessChecked = DateTimeOffset.MinValue;
                await RefreshCompactAccessAsync(force: true);
            }
            else if (mode == "register")
            {
                if (password.Length < 12)
                {
                    _compactAccountMessage.Text = "Пароль должен содержать минимум 12 символов.";
                    return;
                }
                var response = await _api.RegisterAsync(_origin.Text.Trim(), email, password);
                if (response.TryGetProperty("verification_required", out var required) &&
                    required.ValueKind == JsonValueKind.True)
                {
                    _compactPendingEmail = email;
                    _compactAccountMode = "verify";
                    _password.Clear();
                    _compactAccountMessage.Text = "Код отправлен на почту.";
                }
                else _compactAccountMessage.Text = "Проверь почту и подтверди адрес.";
            }
            else if (mode == "verify")
            {
                ++_compactStartEpoch;
                _compactStarting = false;
                _bridge.SetEnabled(false);
                await _api.VerifyEmailAsync(_origin.Text.Trim(),
                    _compactPendingEmail ?? email, _compactCode.Text);
                ResetCompactBenefits();
                _compactCode.Clear();
                _compactAccountMode = "login";
                _compactAccountOpen = false;
                await RefreshDiagnosticsAccessAsync();
                _compactAccessChecked = DateTimeOffset.MinValue;
                await RefreshCompactAccessAsync(force: true);
            }
            else if (mode == "recovery")
            {
                await _api.RequestPasswordResetAsync(email);
                _compactPendingEmail = email;
                _compactAccountMode = "reset";
                _compactAccountMessage.Text = "Если адрес зарегистрирован, код отправлен.";
            }
            else if (mode == "reset")
            {
                if (_compactNewPassword.Text.Length < 12)
                {
                    _compactAccountMessage.Text = "Новый пароль: минимум 12 символов.";
                    return;
                }
                await _api.ResetPasswordAsync(_compactPendingEmail ?? email,
                    _compactCode.Text, _compactNewPassword.Text);
                _compactNewPassword.Clear();
                _compactCode.Clear();
                _compactAccountMode = "login";
                _compactAccountMessage.Text = "Пароль изменён. Войди с новым паролем.";
            }
        }
        catch (Exception ex) { _compactAccountMessage.Text = DescribeAccountError(ex); }
        finally
        {
            _loggingIn = false;
            UpdateSafe(preserveAccountStatus: true);
            RenderCompact();
            LayoutCompact();
        }
    }

    private async void CompactPromoSubmitAsync(object? sender, EventArgs e)
    {
        if (_compactPromoBusy || !_api.IsLoggedIn) return;
        _compactPromoBusy = true;
        _compactPromoSubmit.Enabled = false;
        _compactPromoMessage.ForeColor = Secondary;
        _compactPromoMessage.Text = "Проверяем промокод…";
        LayoutCompact();
        try
        {
            var result = await _api.RedeemPromoAsync(_compactPromoCode.Text);
            _compactPromoMessage.Text =
                result.TryGetProperty("revoked", out var revoked) &&
                revoked.ValueKind == JsonValueKind.True ?
                "Эта активация отозвана." :
                result.TryGetProperty("already_activated", out var existing) &&
                existing.ValueKind == JsonValueKind.True ?
                "Промокод уже активирован." : "Промокод активирован.";
            _compactPromoMessage.ForeColor = Accent;
            _compactPromoCode.Clear();
            _compactAccessChecked = DateTimeOffset.MinValue;
            await RefreshCompactAccessAsync(force: true);
        }
        catch (Exception ex)
        {
            _compactPromoMessage.ForeColor = ColorTranslator.FromHtml("#FF918B");
            _compactPromoMessage.Text = DescribeAccountError(ex);
        }
        finally
        {
            _compactPromoBusy = false;
            _compactPromoSubmit.Enabled = true;
            if (!_closing) LayoutCompact();
        }
    }

    private async void CompactSendSupportAsync(object? sender, EventArgs e)
    {
        if (_compactSupportBusy) return;
        if (!_api.IsLoggedIn)
        {
            _compactSupportMessage.Text = "Войди в аккаунт, чтобы отправить сообщение.";
            _compactAccountOpen = true;
            LayoutCompact();
            return;
        }
        var message = _compactSupportText.Text.Trim();
        var song = _compactSupportKind.SelectedIndex == 1;
        if (!song && message.Length < 3)
        {
            _compactSupportMessage.Text = "Опиши проблему перед отправкой.";
            LayoutCompact();
            return;
        }
        if (song && !GrantValidator.IsTrackId(_bridge.GetPlaybackSnapshot().TrackId))
        {
            _compactSupportMessage.Text = "Запусти песню в Яндексе и повтори.";
            LayoutCompact();
            return;
        }
        _compactSupportBusy = true;
        _compactSupportSubmit.Enabled = false;
        _compactSupportMessage.Text = "Отправляем…";
        LayoutCompact();
        try
        {
            // One bounded snapshot per request key, reused if HTTP retries.
            _compactSupportDiagnostics ??= DiagnosticLog.ExportSupportSnapshot(
                _hostReport?.Version, _nativeInstallState.ToString().ToUpperInvariant(),
                _bridgeStarted, _bridge.Enabled, _installedModule.Version,
                _nativeInstallState == NativeInstallState.Active ?
                    _installedModule.MatchesApplication : null, _bridge.LastSong);
            if (song)
            {
                var categories = new[] { "not_replacing", "wrong_version", "audio_issue", "other" };
                var selected = Math.Clamp(_compactSupportCategory.SelectedIndex, 0, categories.Length - 1);
                await _api.SendSongSupportAsync(message, _compactSupportKey,
                    _bridge.GetPlaybackSnapshot().TrackId, categories[selected], _bridgeStarted, _bridge.Enabled,
                    windowsDiagnostics: _compactSupportDiagnostics);
            }
            else await _api.SendSupportAsync(message, _compactSupportKey,
                diagnostics: _compactSupportDiagnostics);
            DiagnosticLog.Record("SUPPORT_SENT");
            _compactSupportDiagnostics = null;
            _compactSupportKey = Guid.NewGuid();
            _compactSupportText.Clear();
            _compactSupportMessage.Text = "Сообщение отправлено.";
        }
        catch (Exception ex)
        {
            DiagnosticLog.Record("SUPPORT_SEND_FAILED");
            _compactSupportMessage.Text = DescribeAccountError(ex);
        }
        finally
        {
            _compactSupportBusy = false;
            _compactSupportSubmit.Enabled = true;
            if (!_closing) LayoutCompact();
        }
    }

    private long? GetCompactOriginalDuration()
    {
        var playback = _bridge.GetPlaybackSnapshot();
        var known = string.Equals(playback.TrackId, _compactPinnedUploadTrack,
            StringComparison.Ordinal) ? playback.DurationMs : 0;
        if (known >= 1000) return known;
        if (double.TryParse(_compactUploadDuration.Text.Trim().Replace(',', '.'),
                NumberStyles.AllowDecimalPoint, CultureInfo.InvariantCulture, out var seconds) &&
            seconds is >= 1 and <= 86400)
            return (long)Math.Round(seconds * 1000);
        return null;
    }

    private void CompactUploadError(string message)
    {
        _compactUploadNote.Text = message;
        _compactUploadNote.ForeColor = ColorTranslator.FromHtml("#FFBDB7");
        _compactUploadNote.BackColor = _compactUploadBody.BackColor;
        RenderCompact();
        LayoutCompact();
    }

    private async Task CheckCompactFileAsync(int debounceMs = 0)
    {
        if (_compactSelectedAudio is null || _compactUploadView != "form") return;
        var path = _compactSelectedAudio;
        var trackId = _compactPinnedUploadTrack;
        var original = GetCompactOriginalDuration();
        var generation = ++_compactFilePreflightGeneration;
        _compactFileChecking = true;
        _compactAudioPreflight = null;
        _compactPreflightTrack = "";
        _compactPreflightReferenceMs = 0;
        RenderCompact();
        LayoutCompact();
        if (debounceMs > 0) await Task.Delay(debounceMs);
        if (generation != _compactFilePreflightGeneration || _closing ||
            !IsCompactCurrentTrack(trackId) || _compactSelectedAudio != path) return;
        AudioPreflight.Result result;
        try
        {
            result = await AudioPreflight.CheckAsync(path, original);
        }
        catch (Exception)
        {
            result = new AudioPreflight.Result(null, true,
                "Файл не удалось проверить. Выберите другой MP3 или M4A.");
        }
        if (generation != _compactFilePreflightGeneration || _closing ||
            !IsCompactCurrentTrack(trackId) || _compactSelectedAudio != path) return;
        _compactFileChecking = false;
        _compactAudioPreflight = result;
        _compactPreflightTrack = trackId;
        _compactPreflightReferenceMs = original ?? 0;
        _compactUploadNote.Text = "";
        RenderCompact();
        LayoutCompact();
    }

    private async void CompactChooseAudio(object? sender, EventArgs e)
    {
        using var select = new OpenFileDialog
        {
            Title = "Выбери версию песни",
            Filter = "Аудио (*.mp3;*.m4a)|*.mp3;*.m4a",
            RestoreDirectory = true, CheckFileExists = true
        };
        if (select.ShowDialog(this) != DialogResult.OK) return;
        var file = new FileInfo(select.FileName);
        if (file.Length is < 1024 or > AudioPreflight.MaxBytes)
        {
            CompactUploadError("Выберите MP3 или M4A размером до 30 МиБ.");
            return;
        }
        _compactSelectedAudio = file.FullName;
        _compactUploadRequestId = Guid.NewGuid();
        _compactFilePicker.SelectedFile = file.Name + " · " +
            (file.Length / 1_048_576d).ToString("0.0",
                CultureInfo.GetCultureInfo("ru-RU")) + " МиБ";
        // The extension displays this inside its file picker, not a second label.
        _compactFileName.Text = "";
        _compactUploadNote.Text = "";
        _compactUploadNote.ForeColor = Secondary;
        await CheckCompactFileAsync();
    }

    private async void CompactSuggestAsync(object? sender, EventArgs e)
    {
        if (_compactContributionBusy || !_api.IsLoggedIn || _compactSuggestView != "form") return;
        var track = _compactPinnedSuggestTrack;
        if (!IsCompactCurrentTrack(track))
        {
            _compactSuggestNote.Text = "Песня сменилась или её данные обновляются. Открой предложение заново.";
            return;
        }
        _compactContributionBusy = true;
        _compactSuggestSubmit.Enabled = false;
        try
        {
            var current = await _api.GetTrackVersionStatusAsync(track);
            var status = JsonText(current, "status");
            if (status is "approved" or "pending")
            {
                SetCompactPresenceStatus(track, status);
                CompactResult(false, track, status == "approved" ? "Версия уже доступна" : "Версия на проверке",
                    "Песня уже в CELIKOM. Повторное предложение не требуется.");
                return;
            }
            if (status != "none" || !IsCompactCurrentTrack(track))
                throw new ApiFailure(400, "TRACK_CHANGED");

            var playback = _bridge.GetPlaybackSnapshot();
            if (!string.Equals(playback.TrackId, track, StringComparison.Ordinal))
                throw new ApiFailure(400, "TRACK_CHANGED");
            await _api.SuggestTrackAsync(track, playback.Title, playback.Artist);
            if (IsCompactCurrentTrack(track))
            {
                SetCompactPresenceStatus(track, "pending");
                CompactResult(false, track, "Предложение отправлено",
                    "Песня отправлена на рассмотрение. Повторное предложение не требуется.");
            }
            else
            {
                _compactSuggestView = "error";
                _compactSuggestNote.Text = "Предложение по предыдущей песне отправлено.";
            }
        }
        catch (ApiFailure ex) when (ex.Category is "track_pending" or "track_already_approved")
        {
            var status = ex.Category == "track_pending" ? "pending" : "approved";
            SetCompactPresenceStatus(track, status);
            CompactResult(false, track, status == "pending" ? "Версия уже на проверке" : "Версия уже доступна",
                "Песня уже в CELIKOM. Повторное предложение не требуется.");
        }
        catch (Exception ex) { _compactSuggestNote.Text = DescribeAccountError(ex); }
        finally
        {
            _compactContributionBusy = false;
            RenderCompact();
            LayoutCompact();
        }
    }

    private async void CompactUploadAsync(object? sender, EventArgs e)
    {
        if (_compactUploadCancellation is not null)
        {
            var answer = MessageBox.Show(this,
                "Отменить передачу файла? Уже отправленные данные нельзя будет продолжить с того же места.",
                "Отменить загрузку?", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (answer == DialogResult.Yes) _compactUploadCancellation.Cancel();
            return;
        }
        if (_compactUploadView != "form") return;
        var track = _compactPinnedUploadTrack;
        if (!_api.IsLoggedIn || !IsCompactCurrentTrack(track))
        {
            CompactUploadError("Песня сменилась или её данные обновляются. Открой загрузку заново.");
            return;
        }
        if (!_compactRights.Checked)
        {
            CompactUploadError("Подтверди права на файл.");
            return;
        }
        if (_compactSelectedAudio is null || !File.Exists(_compactSelectedAudio))
        {
            CompactUploadError("Выбери MP3 или M4A.");
            return;
        }
        var durationMs = GetCompactOriginalDuration();
        if (durationMs is null)
        {
            CompactUploadError("Не удалось определить длительность текущей песни. Отправка заблокирована.");
            return;
        }
        if (_compactFileChecking || _compactAudioPreflight is not { Blocked: false } ||
            _compactPreflightTrack != track || _compactPreflightReferenceMs != durationMs)
        {
            CompactUploadError("Сначала дождитесь проверки аудиофайла. Неподходящая длительность блокирует загрузку.");
            return;
        }
        using var token = new CancellationTokenSource();
        _compactUploadCancellation = token;
        _compactUploadSubmit.Text = "Отменить";
        _compactUploadSubmit.Enabled = true;
        _compactUploadNote.Text = "Проверяем песню перед отправкой…";
        _compactUploadProgress.Value = 0;
        LayoutCompact();
        try
        {
            var version = await _api.GetTrackVersionStatusAsync(track, token.Token);
            var status = JsonText(version, "status");
            if (status is "approved" or "pending")
            {
                SetCompactPresenceStatus(track, status);
                CompactResult(true, track, status == "approved" ? "Версия уже доступна" : "Трек уже добавлен",
                    "Повторно загружать эту песню не требуется.");
                return;
            }
            if (status != "none" || !IsCompactCurrentTrack(track))
                throw new ApiFailure(400, "TRACK_CHANGED");
            var upload = _compactSelectedAudio;
            if (upload is null) throw new ApiFailure(400, "INVALID_FILE");
            var checkedAgain = await AudioPreflight.CheckAsync(upload, durationMs, token.Token);
            if (checkedAgain.Blocked || !IsCompactCurrentTrack(track))
            {
                _compactAudioPreflight = checkedAgain;
                _compactFileChecking = false;
                CompactUploadError(checkedAgain.Blocked ? checkedAgain.DurationMessage :
                    "Трек изменился. Повторите загрузку.");
                return;
            }
            var currentTrack = _bridge.GetPlaybackSnapshot();
            if (!string.Equals(currentTrack.TrackId, track, StringComparison.Ordinal))
                throw new ApiFailure(400, "TRACK_CHANGED");
            var progress = new Progress<int>(percent =>
            {
                if (_compactUploadCancellation != token || _closing) return;
                _compactUploadProgress.Value = Math.Clamp(percent, 0, 100);
                _compactUploadNote.Text = percent >= 100
                    ? "Файл передан. Ждём ответа сервера…"
                    : "Загружаем: " + percent + "%";
                LayoutCompact();
            });
            await _api.UploadTrackAsync(track, upload, durationMs.Value,
                currentTrack.Title, currentTrack.Artist,
                _compactUploadRequestId, progress, token.Token);
            if (IsCompactCurrentTrack(track))
            {
                SetCompactPresenceStatus(track, "pending");
                CompactResult(true, track, "Отправлено на проверку",
                    "Версия ожидает модерации. Повторная загрузка не требуется.");
            }
            else
            {
                _compactUploadView = "error";
                _compactUploadNote.Text = "Файл предыдущей песни отправлен на проверку.";
            }
            _compactSelectedAudio = null;
            _compactFilePicker.SelectedFile = "";
            _compactFileName.Text = "";
            _compactRights.Checked = false;
            _compactUploadRequestId = Guid.NewGuid();
        }
        catch (OperationCanceledException) { CompactUploadError("Загрузка отменена."); }
        catch (ApiFailure ex) when (ex.Category is "track_pending" or "track_already_approved")
        {
            var status = ex.Category == "track_pending" ? "pending" : "approved";
            SetCompactPresenceStatus(track, status);
            CompactResult(true, track, status == "pending" ? "Трек уже добавлен" : "Версия уже доступна",
                "Эта версия уже есть в CELIKOM, повторная отправка не нужна.");
        }
        catch (Exception ex) { CompactUploadError(DescribeAccountError(ex)); }
        finally
        {
            _compactUploadCancellation = null;
            _compactUploadSubmit.Text = "Отправить на проверку";
            RenderCompact();
            LayoutCompact();
        }
    }

}

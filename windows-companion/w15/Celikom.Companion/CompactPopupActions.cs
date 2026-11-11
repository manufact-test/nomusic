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
            ++_compactAccessGeneration;
            _compactAccess.Text = "Войдите в аккаунт, чтобы начать";
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
        _compactAccess.Text = "Проверяем доступ…";
        try
        {
            JsonElement response;
            try { response = await _api.GetEntitlementAsync(); }
            catch (Exception ex) when (_bridge.Enabled && EntitlementCheckRecovery.IsTransient(ex))
            {
                // A one-off 9-second timeout, 429 or 5xx need not force a manual
                // Stop/Start. One short, bounded GET retry only; no replayed writes.
                DiagnosticLog.Record("ACTIVE_ENTITLEMENT_RETRY");
                await Task.Delay(400);
                using var retryTimeout = new CancellationTokenSource(TimeSpan.FromSeconds(3));
                response = await _api.GetEntitlementAsync(retryTimeout.Token);
                DiagnosticLog.Record("ACTIVE_ENTITLEMENT_RETRY_OK");
            }
            if (!StillSameUser()) return;
            _compactAccess.Text = AccessLabel(response);
            _compactAccessChecked = DateTimeOffset.UtcNow;
            var allowed = PlaybackEntitlement.Allowed(response, DateTimeOffset.UtcNow);
            if (!allowed)
            {
                _resumeAfterNetworkFailure = false; // authoritative deny NEVER reconnects
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
                _resumeAfterNetworkFailure = false;
                _bridge.SetEnabled(true);
                DiagnosticLog.Record("ACTIVE_ENTITLEMENT_RECOVERED");
            }
        }
        catch (Exception ex)
        {
            if (!StillSameUser()) return;
            var transient = EntitlementCheckRecovery.IsTransient(ex);
            if (_bridge.Enabled)
            {
                ++_compactStartEpoch;
                _compactStarting = false;
                _resumeAfterNetworkFailure = transient &&
                    _nativeInstallState == NativeInstallState.Active &&
                    _installedModule.MatchesApplication;
                _bridge.SetEnabled(false); // fail closed until new live authority
                DiagnosticLog.Record(transient ?
                    "ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED" :
                    "ACTIVE_ENTITLEMENT_CHECK_UNAVAILABLE");
            }
            else if (!transient && _resumeAfterNetworkFailure)
            {
                _resumeAfterNetworkFailure = false;
                DiagnosticLog.Record("ACTIVE_ENTITLEMENT_RECOVERY_DENIED");
            }
            _compactAccess.Text = _resumeAfterNetworkFailure
                ? "Нет связи. Подмена приостановлена; повторим проверку автоматически."
                : "Доступ не подтверждён. Подмена выключена.";
        }
        finally { _compactAccessBusy = false; }
    }

    private async Task<string> ReadCompactPresenceAsync(string trackId, bool force)
    {
        if (!GrantValidator.IsTrackId(trackId) || !_api.IsLoggedIn)
            throw new ApiFailure(401, "INVALID_SESSION");
        if (!force && _compactPresenceTrack == trackId &&
            _compactPresenceStatus is "approved" or "pending" or "none" &&
            DateTimeOffset.UtcNow - _compactPresenceChecked < TimeSpan.FromSeconds(15))
            return _compactPresenceStatus;
        if (_compactPresencePending is { IsCompleted: false } &&
            _compactPresencePendingTrack == trackId)
            return await _compactPresencePending;
        async Task<string> Read()
        {
            var result = await _api.GetTrackVersionStatusAsync(trackId);
            var status = JsonText(result, "status");
            if (status is not ("none" or "pending" or "approved"))
                throw new ApiFailure(502, "UPLOAD_STATUS_UNAVAILABLE");
            return status;
        }
        var task = Read();
        _compactPresencePending = task;
        _compactPresencePendingTrack = trackId;
        try
        {
            var status = await task;
            if (_compactPresenceTrack == trackId && _api.IsLoggedIn && !_closing)
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
            }
        }
    }

    private async Task RefreshCompactPresenceAsync(string trackId)
    {
        try { await ReadCompactPresenceAsync(trackId, force: false); }
        catch
        {
            if (_compactPresenceTrack == trackId && !_closing)
            {
                _compactPresenceStatus = "error";
                RenderCompact();
                LayoutCompact();
            }
        }
    }

    private void CompactResult(bool upload, string title, string details)
    {
        if (upload)
        {
            _compactUploadView = "result";
            _compactUploadResultTitle.Text = title;
            _compactUploadResultNote.Text = details;
        }
        else
        {
            _compactSuggestView = "result";
            _compactSuggestResultTitle.Text = title;
            _compactSuggestResultNote.Text = details;
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

        var id = _bridge.LastSong;
        try
        {
            if (!GrantValidator.IsTrackId(id) || !_api.IsLoggedIn)
                throw new ApiFailure(400, "TRACK_REQUIRED");
            var status = await ReadCompactPresenceAsync(id, force: true);
            if (generation != _compactOpenEpoch || _bridge.LastSong != id || !_api.IsLoggedIn)
                return;
            if (status == "approved")
                CompactResult(upload, "Версия уже доступна",
                    "Для этой песни уже есть одобренная версия CELIKOM. Повторная отправка не требуется.");
            else if (status == "pending")
                CompactResult(upload, upload ? "Трек уже добавлен" : "Версия уже на проверке",
                    "Альтернативная версия ожидает проверки. Повторная отправка не требуется.");
            else if (upload)
            {
                _compactPinnedUploadTrack = id;
                _compactUploadView = "form";
                // No permanent placeholder under Send: feedback only appears on demand.
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
        if (song && !GrantValidator.IsTrackId(_bridge.LastSong))
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
                    _bridge.LastSong, categories[selected], _bridgeStarted, _bridge.Enabled,
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
        var known = _bridge.LastTrackDurationMs;
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
            trackId != _bridge.LastSong || _compactSelectedAudio != path) return;
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
            trackId != _bridge.LastSong || _compactSelectedAudio != path) return;
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
        if (!GrantValidator.IsTrackId(track) || track != _bridge.LastSong)
        {
            _compactSuggestNote.Text = "Песня сменилась. Открой предложение заново.";
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
                CompactResult(false, status == "approved" ? "Версия уже доступна" : "Версия на проверке",
                    "Песня уже в CELIKOM. Повторное предложение не требуется.");
                return;
            }
            if (status != "none" || track != _bridge.LastSong)
                throw new ApiFailure(400, "TRACK_CHANGED");
            await _api.SuggestTrackAsync(track, _bridge.LastTrackTitle, _bridge.LastTrackArtist);
            if (_bridge.LastSong == track)
                CompactResult(false, "Предложение отправлено",
                    "Песня отправлена на рассмотрение. Повторное предложение не требуется.");
            else
            {
                _compactSuggestView = "error";
                _compactSuggestNote.Text = "Предложение по предыдущей песне отправлено.";
            }
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
        if (!_api.IsLoggedIn || !GrantValidator.IsTrackId(track) ||
            track != _bridge.LastSong)
        {
            CompactUploadError("Песня изменилась. Открой загрузку заново.");
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
                CompactResult(true, status == "approved" ? "Версия уже доступна" : "Трек уже добавлен",
                    "Повторно загружать эту песню не требуется.");
                return;
            }
            if (status != "none" || track != _bridge.LastSong)
                throw new ApiFailure(400, "TRACK_CHANGED");
            var upload = _compactSelectedAudio;
            if (upload is null) throw new ApiFailure(400, "INVALID_FILE");
            // Independent preflight immediately before multipart body transmission:
            // never upload when the file changed after initial selection.
            var checkedAgain = await AudioPreflight.CheckAsync(upload, durationMs, token.Token);
            if (checkedAgain.Blocked || track != _bridge.LastSong)
            {
                _compactAudioPreflight = checkedAgain;
                _compactFileChecking = false;
                CompactUploadError(checkedAgain.Blocked ? checkedAgain.DurationMessage :
                    "Трек изменился. Повторите загрузку.");
                return;
            }
            var progress = new Progress<int>(percent =>
            {
                if (_compactUploadCancellation != token || _closing) return;
                _compactUploadProgress.Value = Math.Clamp(percent, 0, 100);
                _compactUploadNote.Text = percent >= 100
                    ? "Файл передан. Ждём ответа сервера…"
                    : "Загружаем: " + percent + "%";
                LayoutCompact(); // show dynamic feedback only during actual transfer
            });
            await _api.UploadTrackAsync(track, upload, durationMs.Value,
                _bridge.LastTrackTitle, _bridge.LastTrackArtist,
                _compactUploadRequestId, progress, token.Token);
            if (_bridge.LastSong == track && _compactPresenceTrack == track)
            {
                CompactResult(true, "Отправлено на проверку",
                    "Версия ожидает модерации. Повторная загрузка не требуется.");
                _compactPresenceStatus = "pending";
                _compactPresenceChecked = DateTimeOffset.UtcNow;
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
            CompactResult(true, ex.Category == "track_pending" ? "Трек уже добавлен" : "Версия уже доступна",
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

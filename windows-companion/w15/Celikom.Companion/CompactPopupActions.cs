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
            ++_compactAccessGeneration;
            _compactAccess.Text = "Войдите в аккаунт, чтобы начать";
            return;
        }
        if (_compactAccessBusy) return;
        var generation = ++_compactAccessGeneration;
        if (!_api.IsLoggedIn)
        {
            _compactAccess.Text = "Войдите в аккаунт, чтобы начать";
            return;
        }
        if (_compactAccessBusy) return;
        if (!force && DateTimeOffset.UtcNow - _compactAccessChecked < TimeSpan.FromSeconds(75))
            return;
        _compactAccessBusy = true;
        _compactAccess.Text = "Проверяем доступ…";
        try
        {
            var response = await _api.GetEntitlementAsync();
            if (generation != _compactAccessGeneration || !_api.IsLoggedIn || _closing) return;
            _compactAccess.Text = AccessLabel(response);
            _compactAccessChecked = DateTimeOffset.UtcNow;
        }
        catch
        {
            if (generation == _compactAccessGeneration && !_closing)
                _compactAccess.Text = "Нет связи. Доступ проверяется сервером.";
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
                _compactUploadNote.Text = "Новая версия появится после проверки.";
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
                await _api.LoginAsync(_origin.Text.Trim(), email, password);
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
                await _api.VerifyEmailAsync(_origin.Text.Trim(),
                    _compactPendingEmail ?? email, _compactCode.Text);
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
        _compactPromoMessage.Text = "Проверяем промокод…";
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
            _compactPromoCode.Clear();
            _compactAccessChecked = DateTimeOffset.MinValue;
            await RefreshCompactAccessAsync(force: true);
        }
        catch (Exception ex) { _compactPromoMessage.Text = DescribeAccountError(ex); }
        finally { _compactPromoBusy = false; _compactPromoSubmit.Enabled = true; }
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
            return;
        }
        if (song && !GrantValidator.IsTrackId(_bridge.LastSong))
        {
            _compactSupportMessage.Text = "Запусти песню в Яндексе и повтори.";
            return;
        }
        _compactSupportBusy = true;
        _compactSupportSubmit.Enabled = false;
        _compactSupportMessage.Text = "Отправляем…";
        try
        {
            if (song)
            {
                var categories = new[] { "not_replacing", "wrong_version", "audio_issue", "other" };
                var selected = Math.Clamp(_compactSupportCategory.SelectedIndex, 0, categories.Length - 1);
                await _api.SendSongSupportAsync(message, _compactSupportKey,
                    _bridge.LastSong, categories[selected], _bridgeStarted, _bridge.Enabled);
            }
            else await _api.SendSupportAsync(message, _compactSupportKey);
            _compactSupportKey = Guid.NewGuid();
            _compactSupportText.Clear();
            _compactSupportMessage.Text = "Сообщение отправлено.";
        }
        catch (Exception ex) { _compactSupportMessage.Text = DescribeAccountError(ex); }
        finally { _compactSupportBusy = false; _compactSupportSubmit.Enabled = true; }
    }

    private void CompactChooseAudio(object? sender, EventArgs e)
    {
        using var select = new OpenFileDialog
        {
            Title = "Выбери версию песни", Filter = "Аудио (*.mp3;*.m4a)|*.mp3;*.m4a",
            RestoreDirectory = true, CheckFileExists = true
        };
        if (select.ShowDialog(this) != DialogResult.OK) return;
        var file = new FileInfo(select.FileName);
        if (file.Length is < 1024 or > 31_457_280)
        {
            _compactUploadNote.Text = "Размер: до 30 МиБ.";
            return;
        }
        _compactSelectedAudio = file.FullName;
        _compactUploadRequestId = Guid.NewGuid();
        _compactFilePicker.SelectedFile = file.Name;
        _compactFileName.Text = file.Name.Length > 36 ? file.Name[..33] + "…" : file.Name;
        _compactUploadNote.Text = "";
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
            _compactUploadNote.Text = "Песня изменилась. Открой загрузку заново.";
            return;
        }
        if (!_compactRights.Checked)
        {
            _compactUploadNote.Text = "Подтверди права на файл.";
            return;
        }
        if (_compactSelectedAudio is null || !File.Exists(_compactSelectedAudio))
        {
            _compactUploadNote.Text = "Выбери MP3 или M4A.";
            return;
        }
        var durationMs = _bridge.LastTrackDurationMs;
        if (durationMs < 1000)
        {
            if (!double.TryParse(_compactUploadDuration.Text.Trim().Replace(',', '.'),
                    NumberStyles.AllowDecimalPoint, CultureInfo.InvariantCulture, out var seconds) ||
                seconds < 1 || seconds > 86400)
            {
                _compactUploadNote.Text = "Не удалось получить длительность из Яндекса. Укажи её в секундах.";
                return;
            }
            durationMs = (long)Math.Round(seconds * 1000);
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
            var progress = new Progress<int>(percent =>
            {
                if (_compactUploadCancellation != token || _closing) return;
                _compactUploadProgress.Value = Math.Clamp(percent, 0, 100);
                _compactUploadNote.Text = percent >= 100
                    ? "Файл передан. Ждём ответа сервера…"
                    : "Загружаем: " + percent + "%";
            });
            await _api.UploadTrackAsync(track, upload, durationMs,
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
        catch (OperationCanceledException) { _compactUploadNote.Text = "Загрузка отменена."; }
        catch (ApiFailure ex) when (ex.Category is "track_pending" or "track_already_approved")
        {
            CompactResult(true, ex.Category == "track_pending" ? "Трек уже добавлен" : "Версия уже доступна",
                "Эта версия уже есть в CELIKOM, повторная отправка не нужна.");
        }
        catch (Exception ex) { _compactUploadNote.Text = DescribeAccountError(ex); }
        finally
        {
            _compactUploadCancellation = null;
            _compactUploadSubmit.Text = "Отправить на проверку";
            RenderCompact();
            LayoutCompact();
        }
    }
}

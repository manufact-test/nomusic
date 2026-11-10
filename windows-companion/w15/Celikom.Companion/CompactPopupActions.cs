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
        if (message.Length < 3)
        {
            _compactSupportMessage.Text = "Опиши проблему перед отправкой.";
            return;
        }
        var song = _compactSupportKind.SelectedIndex == 1;
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
        _compactFileName.Text = file.Name.Length > 36 ? file.Name[..33] + "…" : file.Name;
        _compactUploadNote.Text = "";
    }

    private async void CompactSuggestAsync(object? sender, EventArgs e)
    {
        if (_compactContributionBusy || !_api.IsLoggedIn) return;
        var track = _bridge.LastSong;
        if (!GrantValidator.IsTrackId(track))
        {
            _compactSuggestNote.Text = "Сначала запусти песню в Яндексе.";
            return;
        }
        _compactContributionBusy = true;
        _compactSuggestSubmit.Enabled = false;
        try
        {
            var current = await _api.GetTrackVersionStatusAsync(track);
            if (JsonText(current, "status") == "approved")
            {
                _compactSuggestNote.Text = "Для этой песни версия уже доступна.";
                return;
            }
            if (JsonText(current, "status") == "pending")
            {
                _compactSuggestNote.Text = "Песня уже ожидает проверки.";
                return;
            }
            await _api.SuggestTrackAsync(track);
            _compactSuggestNote.Text = "Предложение отправлено.";
        }
        catch (Exception ex) { _compactSuggestNote.Text = DescribeAccountError(ex); }
        finally { _compactContributionBusy = false; _compactSuggestSubmit.Enabled = true; }
    }

    private async void CompactUploadAsync(object? sender, EventArgs e)
    {
        if (_compactUploadCancellation is not null)
        {
            // Pressing the same primary button again cancels the in-flight transfer.
            _compactUploadCancellation.Cancel();
            return;
        }
        var track = _bridge.LastSong;
        if (!_api.IsLoggedIn || !GrantValidator.IsTrackId(track))
        {
            _compactUploadNote.Text = "Войди и запусти песню в Яндексе.";
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
        if (!double.TryParse(_compactUploadDuration.Text.Trim().Replace(',', '.'),
                NumberStyles.AllowDecimalPoint, CultureInfo.InvariantCulture, out var seconds) ||
            seconds < 1 || seconds > 86400)
        {
            _compactUploadNote.Text = "Укажи длительность песни в секундах.";
            return;
        }
        using var token = new CancellationTokenSource();
        _compactUploadCancellation = token;
        _compactUploadSubmit.Text = "Отменить";
        _compactUploadSubmit.Enabled = true;
        _compactUploadNote.Text = "Загружаем файл…";
        try
        {
            var version = await _api.GetTrackVersionStatusAsync(track, token.Token);
            if (JsonText(version, "status") is "approved" or "pending")
            {
                _compactUploadNote.Text = "Версия уже доступна или на проверке.";
                return;
            }
            await _api.UploadTrackAsync(track, _compactSelectedAudio,
                (long)Math.Round(seconds * 1000), token.Token);
            _compactUploadNote.Text = "Отправлено на модерацию.";
            _compactSelectedAudio = null;
            _compactFileName.Text = "";
            _compactRights.Checked = false;
        }
        catch (OperationCanceledException) { _compactUploadNote.Text = "Загрузка отменена."; }
        catch (Exception ex) { _compactUploadNote.Text = DescribeAccountError(ex); }
        finally
        {
            _compactUploadCancellation = null;
            _compactUploadSubmit.Text = "Отправить на проверку";
        }
    }
}

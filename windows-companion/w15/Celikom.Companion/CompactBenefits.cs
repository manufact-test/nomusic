using System.Drawing;
using System.Text.Json;
using System.Windows.Forms;

namespace Celikom.Companion;

/// <summary>Real benefits / referrals popup parity; never auto-creates a code.</summary>
public sealed partial class MainWindow
{
    private readonly PopupButton _compactBenefitsToggle = new();
    private readonly Label _compactBenefitsProgress = new();
    private readonly Label _compactBenefitsRewards = new();
    private readonly Label _compactBenefitsCode = new();
    private readonly Label _compactBenefitsMessage = new();
    private readonly PopupButton _compactBenefitsAction = new();
    private bool _compactBenefitsAvailable;
    private bool _compactBenefitsOpen;
    private bool _compactBenefitsLoaded;
    private bool _compactBenefitsBusy;
    private int _compactBenefitsEpoch;
    private string _compactBenefitsCodeValue = "";
    private bool _compactReferralsEnabled;

    private void BuildCompactBenefits()
    {
        SetupMainButton(_compactBenefitsToggle, "▸ Бонусы и друзья", (_, _) =>
        {
            if (!_compactBenefitsAvailable) return;
            _compactBenefitsOpen = !_compactBenefitsOpen;
            _compactBenefitsToggle.Text = (_compactBenefitsOpen ? "▾" : "▸") + " Бонусы и друзья";
            LayoutCompact();
            if (_compactBenefitsOpen) ScrollCompactTo(_compactAccountFrame);
        });
        _compactBenefitsToggle.Borderless = true;
        _compactBenefitsToggle.TextAlign = ContentAlignment.MiddleLeft;
        _compactBenefitsToggle.ForeColor = Secondary;
        _compactBenefitsToggle.BackColor = Paper;
        _compactBenefitsToggle.Font = new Font("Segoe UI", 8.5F);
        foreach (var label in new[]
        {
            _compactBenefitsProgress, _compactBenefitsRewards,
            _compactBenefitsCode, _compactBenefitsMessage
        })
        {
            label.BackColor = Paper;
            label.ForeColor = Secondary;
            label.Font = new Font("Segoe UI", 8.5F);
            label.AutoEllipsis = false;
        }
        _compactBenefitsCode.ForeColor = Accent;
        _compactBenefitsMessage.ForeColor = Accent;
        SetupMainButton(_compactBenefitsAction, "Создать код приглашения", CompactBenefitsActionAsync);
        foreach (Control child in new Control[] {
            _compactBenefitsToggle, _compactBenefitsProgress, _compactBenefitsRewards,
            _compactBenefitsCode, _compactBenefitsMessage, _compactBenefitsAction
        }) _compactAccountBody.Controls.Add(child);
    }

    private static bool ReadFlag(JsonElement parent, string key)
        => parent.ValueKind == JsonValueKind.Object &&
           parent.TryGetProperty(key, out var prop) && prop.ValueKind == JsonValueKind.True;
    private static int ReadCount(JsonElement parent, string key)
        => parent.ValueKind == JsonValueKind.Object &&
           parent.TryGetProperty(key, out var prop) &&
           prop.ValueKind == JsonValueKind.Number && prop.TryGetInt32(out var n)
           ? Math.Max(0, n) : 0;

    private async Task RefreshCompactBenefitsAsync()
    {
        if (!_api.IsLoggedIn || _compactBenefitsBusy || _compactBenefitsLoaded) return;
        var epoch = ++_compactBenefitsEpoch;
        var account = _api.Email;
        _compactBenefitsBusy = true;
        try
        {
            var config = await _api.GetConfigAsync();
            var features = config.ValueKind == JsonValueKind.Object &&
                config.TryGetProperty("features", out var f) ? f : default;
            var referralsAvailable = ReadFlag(features, "referrals");
            var rewardsAvailable = ReadFlag(features, "rewards");
            if (epoch != _compactBenefitsEpoch || !_api.IsLoggedIn ||
                _api.Email != account || _closing) return;
            _compactBenefitsAvailable = referralsAvailable || rewardsAvailable;
            _compactReferralsEnabled = referralsAvailable;
            if (!_compactBenefitsAvailable) { _compactBenefitsLoaded = true; return; }
            JsonElement refs = default, rewards = default;
            if (referralsAvailable) refs = await _api.GetReferralsAsync();
            if (rewardsAvailable) rewards = await _api.GetRewardsAsync();
            if (epoch != _compactBenefitsEpoch || !_api.IsLoggedIn ||
                _api.Email != account || _closing) return;
            _compactBenefitsCodeValue = JsonText(refs, "code");
            if (_compactBenefitsCodeValue.Length != 0 &&
                !System.Text.RegularExpressions.Regex.IsMatch(
                    _compactBenefitsCodeValue, "^[A-F0-9]{32}$"))
                _compactBenefitsCodeValue = "";
            _compactBenefitsProgress.Text = referralsAvailable
                ? "Зарегистрировались по коду: " + ReadCount(refs, "registered_count") +
                  ". Бонусы за оплату пока недоступны."
                : "";
            var earned = ReadCount(rewards, "earned_contributions");
            var available = ReadCount(rewards, "available_discount_percent");
            var carry = ReadCount(rewards, "carried_discount_percent");
            _compactBenefitsRewards.Text = rewardsAvailable
                ? earned > 0 ? "За одобренные песни: " +
                    ReadCount(rewards, "earned_discount_percent") +
                    "%. Доступно для будущей оплаты: " + available + "%." +
                    (carry > 0 ? " На следующие месяцы: " + carry + "%." : "")
                : "Загрузите версию песни — бонус появится после одобрения."
                : "";
            _compactBenefitsCode.Text = _compactBenefitsCodeValue.Length > 0
                ? _compactBenefitsCodeValue : "";
            _compactBenefitsAction.Text = _compactBenefitsCodeValue.Length > 0
                ? "Скопировать код" : "Создать код приглашения";
            _compactBenefitsMessage.Text = "";
            _compactBenefitsLoaded = true;
        }
        catch
        {
            if (epoch == _compactBenefitsEpoch && !_closing)
            {
                // Fail closed instead of pretending discounts/referrals exist.
                _compactBenefitsAvailable = false;
                _compactBenefitsLoaded = false;
            }
        }
        finally
        {
            if (epoch == _compactBenefitsEpoch)
            {
                _compactBenefitsBusy = false;
                if (!_closing) LayoutCompact();
            }
        }
    }

    private async void CompactBenefitsActionAsync(object? sender, EventArgs e)
    {
        if (!_api.IsLoggedIn || !_compactReferralsEnabled || _compactBenefitsBusy) return;
        if (_compactBenefitsCodeValue.Length != 0)
        {
            try
            {
                Clipboard.SetText(_compactBenefitsCodeValue);
                _compactBenefitsMessage.Text = "Код скопирован.";
            }
            catch { _compactBenefitsMessage.Text = "Скопировать не удалось."; }
            LayoutCompact();
            return;
        }
        _compactBenefitsBusy = true;
        _compactBenefitsAction.Enabled = false;
        _compactBenefitsMessage.Text = "Создаём код…";
        var epoch = ++_compactBenefitsEpoch;
        try
        {
            var result = await _api.CreateReferralCodeAsync();
            if (epoch != _compactBenefitsEpoch || !_api.IsLoggedIn || _closing) return;
            var code = JsonText(result, "code");
            if (!System.Text.RegularExpressions.Regex.IsMatch(code, "^[A-F0-9]{32}$"))
                throw new InvalidOperationException("Invalid referral code");
            _compactBenefitsCodeValue = code;
            _compactBenefitsCode.Text = code;
            _compactBenefitsAction.Text = "Скопировать код";
            _compactBenefitsMessage.Text = "Код готов.";
        }
        catch { if (epoch == _compactBenefitsEpoch) _compactBenefitsMessage.Text = "Не удалось создать код."; }
        finally
        {
            if (epoch == _compactBenefitsEpoch)
            {
                _compactBenefitsBusy = false;
                _compactBenefitsAction.Enabled = true;
                if (!_closing) LayoutCompact();
            }
        }
    }

    private void ResetCompactBenefits()
    {
        ++_compactBenefitsEpoch;
        _compactBenefitsLoaded = false;
        _compactBenefitsBusy = false;
        _compactBenefitsOpen = false;
        _compactBenefitsAvailable = false;
        _compactReferralsEnabled = false;
        _compactBenefitsCodeValue = "";
        _compactBenefitsProgress.Text = "";
        _compactBenefitsRewards.Text = "";
        _compactBenefitsCode.Text = "";
        _compactBenefitsMessage.Text = "";
        _compactBenefitsToggle.Text = "▸ Бонусы и друзья";
    }

    private void HideCompactBenefits()
    {
        foreach (var control in new Control[] {
            _compactBenefitsToggle, _compactBenefitsProgress, _compactBenefitsRewards,
            _compactBenefitsCode, _compactBenefitsMessage, _compactBenefitsAction
        }) control.Visible = false;
    }

    private int CompactBenefitsHeight()
    {
        if (!_compactBenefitsAvailable) return 0;
        int height = 36;
        if (!_compactBenefitsOpen) return height;
        if (_compactBenefitsProgress.Text.Length != 0) height += 56;
        if (_compactBenefitsRewards.Text.Length != 0) height += 58;
        if (_compactBenefitsCodeValue.Length != 0) height += 30;
        if (_compactReferralsEnabled) height += 46;
        if (_compactBenefitsMessage.Text.Length != 0) height += 38;
        return height;
    }

    private void LayoutCompactBenefits(int width, ref int y)
    {
        HideCompactBenefits();
        if (!_compactBenefitsAvailable) return;
        Place(_compactBenefitsToggle, _compactAccountBody, 0, y, width, 33);
        y += 36;
        if (!_compactBenefitsOpen) return;
        if (_compactBenefitsProgress.Text.Length != 0)
        {
            Place(_compactBenefitsProgress, _compactAccountBody, 0, y, width, 53);
            y += 56;
        }
        if (_compactBenefitsRewards.Text.Length != 0)
        {
            Place(_compactBenefitsRewards, _compactAccountBody, 0, y, width, 55);
            y += 58;
        }
        if (_compactBenefitsCodeValue.Length != 0)
        {
            Place(_compactBenefitsCode, _compactAccountBody, 0, y, width, 27);
            y += 30;
        }
        if (_compactReferralsEnabled)
        {
            Place(_compactBenefitsAction, _compactAccountBody, 0, y, width, 40);
            y += 46;
        }
        if (_compactBenefitsMessage.Text.Length != 0)
        {
            Place(_compactBenefitsMessage, _compactAccountBody, 0, y, width, 35);
            y += 38;
        }
    }
}

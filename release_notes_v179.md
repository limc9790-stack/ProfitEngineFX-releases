# ProfitEngineFX v1.7.9

**Release date:** 2026-05-05
**Status:** stable

## What's new

v1.7.9 addresses 16 issues reported against v1.7.8 (six critical bugs, two
logic improvements, six UX upgrades, and two new strategy filters).

### Critical bugs fixed

1. **Multi-TP partial closes now actually fire.** Pre-1.7.9 the engine
   announced TP1/TP2/TP3 plans in Telegram but never sent the partial-close
   orders to MT5. The position-management tick now runs every 30s (was 2 min)
   and emits a `POSITION_TICK: scanning N positions` line so users can verify
   the cluster is firing.
2. **Layering ladders place at distinct prices, with per-leg Telegram
   alerts.** Pyramid / Grid / Iceberg now emit `Layering Started` followed by
   one `Layer i/N placed @ price (#ticket)` alert per accepted leg. Iceberg
   uses a 0.25 % per-step price ladder by default, fixing the v1.7.8
   "all 4 layers at the same price" bug on indices.
3. **Breakeven actually moves SL.** The `_manage_breakeven` tick already
   called `mt5.order_send(TRADE_ACTION_SLTP)`; the perceived "didn't fire"
   bug was the 2-min cadence. Cadence is now configurable via
   `position_check_interval_sec` (default 30).
4. **Position-management tick is observable.** Every cycle prints the
   `POSITION_TICK: scanning N open position(s)` header so engine_crash.log
   shows whether BE / Multi-TP / partial-close is even getting a chance to
   evaluate this tick.
5. **Daily-loss accounting is SGT-anchored.** Realised P&L for "today" is
   now bounded by SGT 00:00 (was UTC 00:00, which appeared to "reset" at
   SGT 08:00). The new `_get_today_start_sgt()` / `_calculate_daily_loss_sgt()`
   helpers feed both `_realized_pnl_today` and the daily-limit alert.
6. **Session toggles actually gate trades.** `_is_session_active` reads the
   top-level `<session>_session_enabled` keys the Settings UI was already
   writing; the legacy nested `sessions` dict is still honoured for
   back-compat with old `settings.json` files.

### Logic improvements

7. **BOS requires a closed-bar break.** `m15_bos` now evaluates against
   `c[-2]` (the most-recent fully-closed bar) by default. Configurable via
   `require_bos_close_confirmed`. Eliminates the "predicted BOS" entries
   where a wick approached but didn't close past the swing.
8. **Telegram alerts match actual behaviour.** The "TP Plan / 止盈计划"
   block is suppressed when `multi_tp_enabled=false` or in classic mode.
   Layering started/per-leg alerts only fire when `layering_mode != "off"`.
   Session-disabled skips no longer spam the chat.

### UX / features

9. **Login flow consolidation + auto-save credentials.** LicenseScreen
   defaults to the Login tab on every launch (was Register for new users).
   On successful server login, the (email, password) pair is encrypted via
   Electron `safeStorage` (Windows DPAPI / macOS Keychain / Linux
   secret-service) and persisted, the local app password is silently set
   to the same value, and the next launch silent-logins straight to the
   dashboard. The Remember Me checkbox has been removed — saving is the
   default. Sign Out and Reset App both clear the credential blob.
10. **CHOCH (Change of Character) detection.** New analyst detector
    surfaces opposite-direction structure breaks against the prior trend,
    used as both an entry confirmation and an early-exit signal. Exposed
    via `choch_detection_enabled`, `choch_use_as_entry`, `choch_use_as_exit`.
11. **Daily-limit Telegram alert is one-shot per SGT day.** Pre-1.7.9
    every scan that hit the budget re-emitted "Daily budget exhausted".
    Now: a single ⚠️ alert when the limit is first hit, then 🌅 "Daily
    reset at SGT midnight" when the budget refreshes the next calendar day.
12. **Classic mode lot sizing + per-symbol SL buffer.** Classic mode now
    pads the literal zone-edge SL by a per-symbol pip buffer
    (`classic_sl_buffer_pips`, defaults: XAUUSD 5, BTCUSD 50, ETHUSD 30,
    EURUSD 2, GBPJPY 4, DJI30 3, SPX500 1, NDX100 5; general fallback 3).
    Fixes the v1.7.8 "11.94 lot EURUSD on a $25K account" bug caused by
    `risk_usd / sl_dist` exploding when the zone collapsed to a few pips.
13. **Forgot Password via Supabase.** LicenseScreen Login tab has a new
    "Forgot password?" link that POSTs to `/api/auth/reset-password`. The
    server (Render) needs a small `/api/auth/reset-password` endpoint that
    calls `supabase.auth.resetPasswordForEmail(email, ...)` — see "Server
    follow-up" below.
14. **"🛡️ Risk Review" Telegram section removed.** Per-symbol scan output
    already surfaces the same reject reasons; the duplicate section bloated
    every digest. Single-line "no qualified setups" message kept.

### New strategy filters

15. **Require BOS or CHOCH before entry.** New `require_bos_or_choch`
    setting (default ON) blocks entries that lack EITHER a confirmed-close
    BOS in the trade direction OR a directional CHOCH. Applied in both
    Classic and v1.7.x scoring pipelines.
16. **HTF (H4) trend alignment filter.** New `htf_trend_filter` /
    `htf_timeframe` settings (default ON, H4) refuse BUY against an HTF
    bearish (LH+LL) read and SELL against an HTF bullish (HH+HL) read.
    Ranging HTF is permissive (the gate doesn't fire) so pullback trades
    still go through. Applied in both pipelines.

## Settings

New Settings → Order Execution section:
- "Position Check Interval (sec)" (default 30 — replaces the legacy
  minute-granularity field).
- "Structural Confirmation (v1.7.9)" — toggles for `require_bos_close_confirmed`,
  `choch_detection_enabled`, `choch_use_as_entry`, `choch_use_as_exit`,
  `require_bos_or_choch`, `htf_trend_filter`, `htf_timeframe`.
- "Classic SL Buffer (v1.7.9)" — default-pip field plus per-symbol table.

## Server follow-up

The `/api/auth/reset-password` endpoint must be added to the Render Flask
app (`server/routes/auth.py`):

```python
from flask import request, jsonify
from supabase_admin import supabase  # adjust to existing import

@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    email = (request.json or {}).get('email', '').strip()
    if not email:
        return jsonify(error='email required'), 400
    try:
        supabase.auth.reset_password_for_email(
            email,
            options={'redirect_to': 'https://profitenginefx.onrender.com/reset-callback'},
        )
        return jsonify(ok=True)
    except Exception as exc:
        return jsonify(error=str(exc)), 500
```

A static `/reset-callback` page (any minimal HTML that says "Password
reset — please return to the desktop app and sign in") is enough to
satisfy the Supabase redirect.

## Files changed

- `engine/trading_engine.py` — SGT helpers, position-tick log, layering
  alerts, daily-limit one-shot alert, defaults block.
- `engine/agents/analyst.py` — close-confirmed BOS, CHOCH detector, HTF
  trend helper, threading the new toggles through.
- `engine/agents/strategist.py` — `_check_v179_structural_gates()` shared
  by `score_symbol` and `score_symbol_classic`, classic SL buffer.
- `engine/telegram_alerts.py` — "Risk Review" section dropped, multi-TP
  block gated on `multi_tp_enabled` + `classic_mode`.
- `main.js` — `auth:saveCredentials` / `auth:loadCredentials` / `auth:clearCredentials`
  IPC backed by Electron `safeStorage`.
- `main/preload.js` — exposes the new IPCs as `window.api.auth.*Credentials`.
- `renderer/src/App.jsx` — silent-login on launch, clear creds on logout.
- `renderer/src/pages/LicenseScreen.jsx` — Login tab default, save creds
  + setup local password on success, Forgot password Supabase link.
- `renderer/src/pages/LoginScreen.jsx` — Remember Me checkbox removed,
  always-save credentials, clear creds on Reset App.
- `renderer/src/pages/Settings.jsx` — Structural Confirmation +
  Classic SL Buffer sections, position-check seconds field.

## Build

`npm run build:no-renderer` (Nuitka 17 min + electron-builder 2 min).

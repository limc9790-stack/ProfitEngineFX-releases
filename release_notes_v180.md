# ProfitEngineFX v1.8.0 — Risk-Control Hardening

Released: May 2026

## Why this release

v1.7.9 was a 16-fix release that landed major behavioural cleanups (real
multi-TP fires, CHOCH detection, real BE moves, SGT-aligned daily loss).
Live trading on v1.7.9 surfaced two critical bugs that motivated v1.8.0:

1. **Per-trade risk could still overflow.** A tight SL combined with a
   small stop distance produced an 11.94-lot EURUSD on a $25K account —
   the strategist's `calc_lot` and the engine's per-symbol caps both
   passed it through. Risk management was effectively disabled.
2. **Asian-session toggle silently inverted.** Users who turned the
   Asian session ON in the UI saw the engine log "Asian session
   disabled" because the UI was writing one key (`asian_session_enabled`)
   while the engine read another path. Settings drift like
   `min_confidence=660` was getting through too.

v1.8.0 closes both with belt-and-braces validation: every numeric
setting is range-checked at three layers (UI clamp → IPC normalize on
save → engine normalize on load), and every lot calculation passes
through a hard guardrail right before order placement.

## What changed

### 🔴 Critical — hard risk guardrails

1. **`enforce_max_risk_per_trade()` guardrail.** Runs after every Classic /
   Advanced / Layering lot computation. Caps the worst-case loss at
   `min(risk_per_trade_percent, max_loss_per_trade_pct)` of balance —
   no matter what other knobs produced the lot. Logs `RISK_GUARDRAIL`
   and fires a Telegram alert when it shrinks a lot. The 11.94-lot
   EURUSD now becomes 0.51 (the real 1% risk lot) before `order_send`
   is called.

2. **Smart portfolio lot calculator.** New
   `_calculate_lot_smart_portfolio()` aggregates committed worst-case
   risk across every open EA-magic position AND pending order, computes
   remaining headroom under `max_portfolio_risk_percent` (default 5%),
   and either trims the new lot to fit or skips the trade entirely
   (`PORTFOLIO_FULL`). Backed by a reusable
   `aggregate_portfolio_risk_usd()` helper in `engine/agents/risk.py`.

3. **Asian session toggle alignment.** UI Toggle, settings.json, and
   engine `_is_session_active` now read the same canonical key
   (`<name>_session_enabled`). `normalize_settings()` realigns the two
   forms on every load and the renderer's `normalizeSettings()` mirrors
   the alignment on every Save. Engine logs `SESSION_CHECK: Asian=ON,
   London=ON, NewYork=ON` at startup so users / support can verify the
   bot saw the same state the UI is showing.

### 🟡 Settings-defence layers

4. **UI input min/max clamping.** Every numeric field now has HTML5
   `min` / `max` / `step` attributes plus an inline
   "Must be 0–10" / "Must be 50–100%" error. Save Settings is disabled
   while any field is out of range. A new shared module
   `renderer/src/utils/settings_validator.js` centralises the ranges
   for ~70 numeric settings.

5. **Engine startup normalize.** `normalize_settings()` runs on every
   `_load_settings()` call. Out-of-range / non-numeric / missing values
   snap to the spec defaults; the engine logs every fix to the `.log`
   file, persists the corrected values, and fires a Telegram alert.

6. **Default-value review.** `SETTING_DEFAULTS` table in
   `engine/trading_engine.py` now ships sane min/max for every numeric
   setting. Mirror tables in `renderer/src/utils/settings_validator.js`
   and `main/settings_validator.cjs` keep the three layers in sync.

### 🟢 Save-time normalize

7. **IPC normalize on save.** `main.js`'s `settings:save` /
   `autoTrading:start` / `engine:pipeline` handlers route every settings
   write through `normalizeSettings()` before persistence. Anything that
   was auto-fixed gets logged to `engine_crash.log` and sent to
   Telegram.

### 🧊 Smart Layering — unified group SL/TP + auto-profit-lock

8. **Min-lot per layer + grouped exit.** New
   `layering_use_min_lot_per_layer` opt-in flag turns any existing
   layering mode (pyramid / grid / iceberg) into a Smart-Layering
   workflow:

   * Every leg — primary AND children — requests the broker's
     `volume_min`, so worst-case loss per leg is bounded by the smallest
     contract the broker will fill.
   * Every leg's MT5 comment carries a compact `G<ts8><dir1>` group
     token (e.g. `PEFX G30000000B L3`) so the engine can later bucket
     all legs of one signal together.
   * Three new caps stop the ladder up-front: `layering_max_layers`
     (count), `layering_max_total_risk_pct` (worst-case $),
     `layering_max_total_lot` (cumulative volume). Hit any cap and the
     remaining legs simply don't fire.
   * A new `_manage_layer_groups()` tick adds two group-level exits
     on top of the per-leg broker SL/TP:
     * **Profit-lock** — when summed P&amp;L (profit + swap +
       commission) across the group reaches
       `layering_auto_close_profit_pct` of balance, every position is
       closed and every pending in the group is cancelled. Logs
       `GROUP_PROFIT_LOCK` and fires a Telegram alert.
     * **Shared SL/TP propagation** — when one leg's broker-side
       SL/TP fires (the position vanishes), any pending orders still
       open in the same group are cancelled so we don't fill into a
       protected exit that no longer applies. Logs `GROUP_LEG_GONE`.
   * Off by default. Existing pyramid / grid / iceberg behaviour is
     untouched until the user flips the flag in Settings.

## Files touched

- `engine/trading_engine.py` — risk guardrail, smart portfolio lot,
  `normalize_settings()`, `SETTING_DEFAULTS` table, session-check log,
  `_save_settings`, `_send_normalize_alert`, Smart-Layering helpers
  (`_make_group_id`, `_extract_group_id`, `_close_all_in_group`,
  `_manage_layer_groups`), `_apply_layering` group-mode integration,
  `_execute_smart_order` group-ID tagging + min-lot override, tick
  poller hook.
- `engine/agents/risk.py` — portfolio risk aggregation
  (`aggregate_portfolio_risk_usd`).
- `renderer/src/pages/Settings.jsx` — input min/max validation,
  Save-button gating, full normalize on load + save.
- `renderer/src/utils/settings_validator.js` — NEW. Shared
  RANGES + clamp / validate / normalize helpers (now incl. the four
  Smart-Layering caps).
- `main/settings_validator.cjs` — NEW. CommonJS mirror for the Electron
  main process (kept in sync with the renderer module).
- `main.js` — IPC normalize-on-save with Telegram alert + engine_crash
  breadcrumb.
- `package.json` — bumped 1.7.9 → 1.8.0.

## Upgrading

Standard `ProfitEngineFX.Setup.1.8.0.exe` over the previous install.
Auto-update will fetch the new installer from the releases repo on the
next launch. No settings.json migration required — out-of-range values
are auto-fixed silently on first load (with a Telegram heads-up if
configured).

## Verifying the fixes

After upgrade, in `engine_crash.log` watch for:

- `ENGINE_START v1.8.0` — confirms the new build is running.
- `SESSION_CHECK: Asian=ON, London=ON, NewYork=ON` — startup snapshot
  of session toggle state. If this disagrees with what the UI is
  showing, raise it as a bug.
- `SETTINGS_NORMALIZE: auto-fixed N value(s)` — only appears if your
  settings.json had drift. The corrected values are persisted
  immediately.
- `RISK_GUARDRAIL: <SYM> lot X→Y` — fires whenever the per-trade hard
  cap shrunk a lot. Should be rare on a clean settings.json — a
  frequent flood means risk_per_trade_percent or
  max_loss_per_trade_pct disagrees with the strategist's lot math
  (open a bug).
- `PORTFOLIO_TRIM: <SYM> X→Y (remaining=$Z)` — portfolio cap engaged.
- `PORTFOLIO_FULL: <SYM> skipped` — portfolio cap exhausted; no new
  trades until existing positions close or hit BE.
- `GROUP_LAYER_PRIMARY: <SYM> <DIR> X→Ymin group=G<ts><dir>` — Smart
  Layering primary leg shrunk to broker volume_min and tagged with the
  group ID. Only fires when `layering_use_min_lot_per_layer` is on.
- `LAYER_GROUP_CAP: <SYM> stopping (max_layers=N | max_total_lot=L |
  max_total_risk=$X)` — the Smart-Layering ladder hit one of its
  cumulative caps and stopped placing further legs.
- `GROUP_PROFIT_LOCK: G<ts><dir> +$X >= $Y` — group profit-lock
  fired; all positions closed + pendings cancelled.
- `GROUP_LEG_GONE: G<ts><dir> all positions vanished, cancelling N
  surviving pending(s)` — broker hit shared SL/TP on every leg; the
  engine cleaned up surviving pendings.

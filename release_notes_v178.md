# ProfitEngineFX v1.7.8 — Classic v1.5.4 Mode + Critical Fixes

Release date: 2026-05-05

This release introduces a master **Classic v1.5.4 Mode** toggle (defaulted ON
for every new and upgrade install), restores the simple pre-1.7 trade pipeline
many users preferred, and ships a stack of correctness fixes for live trading.

## Highlights

### Classic v1.5.4 Mode (default ON)

A new master switch in **Settings** at the top of the page. When ON:

- Strategist runs pattern-only scoring (BG, ICT-OB, FVG, BOS, QM, MOMENTUM
  family, WAVE_DEF) — same code path as v1.5.4.
- SL is placed flush against the order-block / break-and-retest zone edge
  with no extra ATR cushion.
- TP is a single structural target past `min_rr × SL` (liquidity → BOS →
  FVG → OB), falls back to `entry ± min_rr × SL` when nothing qualifies.
- Multi-TP, layering, regime detection, smart-SL anchor, tick-driven BE,
  scout-scale entry, counter-wick guard, require-trigger-candle and the
  news cancel-pending sweep are **globally suppressed**.
- Decision matches by `(symbol, direction)` only — TF / strategy filters
  off — and serves the bundled per-preset baseline backtest cache as
  `agent_approved_strategies.json` so a fresh install trades on day 1
  without running a backtest.

Flip OFF to expose the full advanced settings stack and re-enable any
v1.7.x feature individually.

### Critical fixes

- **#660-score bug**: `verifier_min_score` default lowered from 8 to 6 to
  match the 0–10 scale used by `score_symbol`. The defensive `[1,10]`
  clamp in `risk.py` already snaps a stale `min_confidence=660` value
  back into range and writes a warning to `engine_crash.log`.
- **Settings persistence**: `_set_setting` now reads the on-disk user
  layer, mutates the single key being written, and `os.replace`s the
  file atomically. Previously the engine flushed the merged-with-
  DEFAULTS in-memory dict back to disk, which silently overrode user
  intent on every migration write.
- **Trading sessions actually gate execution**: new `_is_session_active`
  helper checks the current UTC hour against the user's London / New York /
  Asian on/off toggles. A signal that fires inside a disabled session is
  rejected with `_last_order_error = "SESSION_DISABLED"` and a Telegram
  notice ("Asian session disabled — skipping XAUUSD signal").
- **Layering same-price bug (#5)**: iceberg now uses a **percentage**
  ladder (0.25% / 0.5% / 0.75% of primary price between slices) by
  default. The old pip-based ladder collapsed to identical prices on
  indices (DJI30, NDX100) where `info.point` is large. Pyramid and grid
  already used ATR-based spacing — those paths were already correct.
- **Telegram lot mismatch (#6)**: `_execute_smart_order` now reads
  `result.volume` (broker-confirmed) instead of the pre-clamp request
  volume, and surfaces a `LOT_BROKER_RESHAPE` log line whenever the
  broker rounded the requested lot. Telegram alerts and the scan
  summary now match what the broker terminal shows.
- **Direct baseline use**: `bypass_verifier_approval` now defaults to
  `True`, so a fresh install trades the bundled preset-baseline cache
  immediately. Users who run their own backtest can flip it OFF in
  **Settings → Verifier**.

### Logic changes

- **`ranging_strategy`** default flipped from `"mean_reversion"` to
  `"skip"`. Live results showed mean-reversion fading into BB edges lost
  money on most prop-firm symbols. The "no trade is the best trade"
  default keeps the engine out of low-ADX regimes by default; demo users
  who want to test mean-reversion can flip it back in Settings.
- **TF loose match**: already in v1.2.0+ — `_match_approved_combo`
  matches by `(symbol, direction)` only. Confirmed unchanged.

### UX

- **Login: Remember Me** checkbox. When ticked, the email is persisted in
  `localStorage` so the next launch pre-fills the email field.
- **Login: Reset Password** link in the Forgot Password info-box opens
  the website's password-reset page (`/#reset`) directly in the user's
  default browser.
- **Sign Out → auto reset**: clicking Sign Out now stops the engine,
  clears `license.json` + `auth.json` + the renderer's Remember Me
  hint, and force-reloads the renderer so the next user lands on a
  clean license screen.
- **Session toggles** now write both the legacy nested `sessions` dict
  AND flat `<name>_session_enabled` keys for forward compatibility.

## Files changed

- `engine/trading_engine.py` — Classic-mode dispatch, session check,
  `_set_setting` atomic write, layering iceberg percentage ladder,
  `result.volume` propagation, default-settings updates.
- `engine/agents/strategist.py` — `score_symbol_classic` pattern-only
  branch + early-return at the top of `score_symbol`.
- `renderer/src/pages/Settings.jsx` — Classic Mode toggle banner,
  session-toggle flat-key writes, `classic_mode_enabled` default.
- `renderer/src/pages/LoginScreen.jsx` — Remember Me, password reset
  link.
- `renderer/src/App.jsx` — `handleLogout` now clears license cache +
  Remember Me + force-reloads.
- `package.json` — version bump 1.7.7 → 1.7.8.

## Build

Standard installer build:

```powershell
cd C:\Dev\ProfitEngineFX\desktop-app
cd renderer ; npx vite build ; cd ..
npm run build:no-renderer
```

Output:
`dist/ProfitEngineFX Setup 1.7.8.exe`

Then run `publish-1.7.8.ps1` (provided alongside this file) to:

1. Copy the installer to the dotted-name path.
2. Update `C:\Dev\ProfitEngineFX-releases\index.html` (3 spots).
3. Commit + push to `github.com/limc9790-stack/ProfitEngineFX-releases`.
4. Cut a `v1.7.8` GitHub release with the installer attached.

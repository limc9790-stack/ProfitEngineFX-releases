# ProfitEngineFX v1.7.7

Released: May 2026 — supersedes the v1.7.5 release (which had a
broken Auto Daily Update flow). v1.7.7 ships **all** the v1.7.6
bug fixes plus several feature upgrades that grew out of live
testing: structural TP picker, hardened mean reversion (now with
explicit N-bar range mechanics), auto-reset on launch, and a
DevTools lockdown for packaged installs.

Existing v1.7.5 users **must upgrade** — the auto daily update in
v1.7.5 silently produced 0 approved strategies every run.

## 🐛 Critical bug fixes

### Auto Daily Update produced 0 approved strategies (v1.7.5)
`_run_auto_daily_update` passed only `{phase2}` to the backtester.
The matrix runner saw an empty symbols list, iterated nothing,
finished in ~38 seconds, and wrote zero rows to
`backtest_cache.json` — verifier then approved nothing. Manual
backtest worked because `main.js` filled the full config. v1.7.7
mirrors that build: 8-symbol canonical list, every TF the live
scan uses, BOTH directions, and `backtest_days` from settings.
Expected runtime jumps from 38 s to 5–15 min, and the verifier
produces real approval counts.

### Strategist crash in ranging-regime path
`score_symbol_ranging` did `len(rates.get("close") or []) < 30`
which raised `ValueError: The truth value of an array with more
than one element is ambiguous` because `get_rates` returns numpy
arrays. Replaced with explicit `is None` + length guards.

### detect_market_regime data-availability check
The v1.7.5 condition `not rates.get("close") is not None` was a
typo that worked by accident. Cleaned up to a clear `is None` +
minimum-bar-count check.

### Telegram alert reported pre-clamp lot
Telegram alerts read `signal["lot"]` (strategist's pre-clamp
output) instead of the actual lot placed on MT5. Caused user
confusion when Global Max Lot Size or broker volume_min/max
clamped the executed lot to a different value (e.g. signal said
0.1, MT5 had 0.01). v1.7.7 stores the actual placed lot in
`sig["execution"]["lot"]` and overrides `sig["lot"]` before any
downstream alert so every consumer reports the same number.

### Landing page UTF-8 mojibake on publish
`Set-Content` in publish-1.7.5.ps1 used Windows PowerShell 5.1
default ANSI encoding, which mojibaked every emoji, em-dash,
middle-dot, and check mark in the landing page (Windows logo
emoji rendered as `??`). v1.7.7 publish script uses
`[System.IO.File]::ReadAllText/WriteAllText` with explicit UTF-8
(no BOM) and a sanity scan for `�` / `??` after writing.

## ✨ Feature upgrades

### Structural TP picker
Single-TP path walks every recent swing-high/low, liquidity sweep,
BOS target, FVG, and order block in priority order
(liquidity > BOS > FVG > OB) and picks the **nearest** level past
`min_rr × SL`. The selected price is then pulled back by
`tp_structural_buffer_pips` (default 3) so close prints don't
slide right past the level. New settings on Order Execution →
Take-Profit Placement:

- **Place TP at structural level** (default ON) — toggles the picker
- **Require structural TP at Min RR** (default OFF) — when ON,
  signals whose nearest structural target falls short of Min RR
  are REJECTED with a clear reason rather than placing a pure
  RR-multiple TP. Filters out marginal setups; expect fewer
  trades but higher edge.
- **TP Pullback Buffer (pips)** (default 3)

### Hardened mean reversion — explicit N-bar range
v1.7.5's BB-touch entry was a knife-catch. v1.7.6 added wick
rejection + H1 ADX guard. v1.7.7 replaces Bollinger ±2σ for SL/TP
placement with the explicit lookback range (last N M15 bars'
lowest low and highest high). The structural rules now read:

- **Range bottom / top** = `min(lows[-N:])` / `max(highs[-N:])`
- **Range mid** = average of the two
- **Wick rejection trigger** still uses BB ±2σ to spot
  "spike + close back inside" bars (cleaner statistical edge for
  trigger detection)
- **SL** pinned to the structural range edge ± a 5-pip buffer —
  not the BB band, not the wick. Any normal pullback that
  doesn't break the range cleanly keeps the trade alive.
- **TP** at the range mid — the textbook "easier hit" target.
- **Entry zone gate** — BUY only fires when current price sits
  within the bottom `entry_zone_pct` of the range (default 25%);
  SELL only at the top 25%. Prevents the "BUY at 78599 with
  range 78100–78700" knife-catch entries the BB-only logic
  produced.
- **H1 ADX guard** still active — won't mean-revert against a
  trending H1.

New settings on Order Execution → Market Regime Detection →
Mean-Reversion Range Tuning:
- **Range Lookback (M15 bars)** (default 30)
- **Entry Zone (% of range)** (default 25)

### Login / Register UX simplified
Removed the Confirm Password field. The login form is now a single
Email + Password pair regardless of whether a local password
exists. First-time users: the typed password is silently saved as
the local password — no separate "Create Account" step. New
"Register on website" link opens the pricing page in the user's
default browser via a new `window.api.shell.openExternal` IPC
bridge (URL scheme locked to http(s)).

### Auto-reset on every launch
License-cache freshness was unreliable in v1.7.5 — boot-time
`license:check` passed but the engine's runtime validation
rejected the same token, manifesting as "License failed" the
moment the user pressed Auto Trading or Start Single Analysis.
Manually clicking Reset App fixed it, but only until the next
launch. v1.7.7 wipes `auth.json` + `license.json` + `.bak` +
`lock` automatically on every app launch so every run starts
with a fresh server-validated license and a re-authenticated
session.

### DevTools disabled in packaged installer
v1.7.5 auto-opened Chrome DevTools and responded to F12 /
Ctrl+Shift+I in production. v1.7.7 gates both behind
`!app.isPackaged` so end users never see the developer panel,
but the dev-from-source workflow (`npm start`) keeps DevTools
available.

## 🗂 Resources

### Bundled baseline three-file set
The installer ships all three baseline artefacts in
`engine/agents/`:

- `baseline_bars_archive.db` (~24 MB, 280 K bars across 8 symbols × 4 TFs)
- `baseline_backtest_cache.json` (was missing in v1.7.5 ship)
- `baseline_manifest.json` (was missing in v1.7.5 ship)

The cache + manifest are what enables the verifier's WR-blend on
new installs — without them, fresh users had to wait their first
Auto Daily Update before the verifier could approve anything.

## Files touched

- `engine/trading_engine.py` — auto-update config fix, telegram
  lot reporting fix, new ranging settings
- `engine/agents/strategist.py` — numpy hotfix, regime-detect
  cleanup, structural TP picker, N-bar range mean reversion with
  wick rejection + entry zone gate
- `engine/agents/baseline_bars_archive.db` + cache + manifest
- `renderer/src/pages/LoginScreen.jsx` — single-form login +
  "Register on website" link
- `renderer/src/pages/Settings.jsx` — Take-Profit Placement
  section, Mean-Reversion Range Tuning section
- `main.js` — auto-reset on app boot, DevTools gated on
  `!app.isPackaged`, `shell:openExternal` IPC handler
- `main/preload.js` — exposes `window.api.shell.openExternal`
- `package.json` — version 1.7.7
- `publish-1.7.7.ps1` — UTF-8 NoBOM landing page rewrite +
  release-create fallback to upload --clobber

## Upgrade notes

No settings migration required. New keys default to safe values
that preserve v1.7.4 behaviour out of the box (regime detection
defaults to skip-ranging on first surface, TP structural picker
ON, mean-reversion uses 30-bar lookback / 25% entry zone). The
auto-reset on launch wipes any locally cached login session — set
up your license auto-fill workflow or be ready to re-paste the
key each launch.

Mean-reversion users who tuned `ranging_strategy` specifically
should re-test — the new range-edge entry gate fires far less
often than the v1.7.5/v1.7.6 BB-touch trigger. Signal volume in
chop markets drops noticeably; surviving signals have meaningfully
better RR.

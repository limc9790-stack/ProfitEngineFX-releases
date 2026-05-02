# ProfitEngineFX v1.7.6

Released: May 2026 — bugfix release for v1.7.5 plus four feature
upgrades. Existing v1.7.5 users should upgrade — the auto daily update
in v1.7.5 was effectively non-functional.

## 🐛 Critical bugfixes

### Auto Daily Update produced 0 approved strategies
v1.7.5's `_run_auto_daily_update` passed only `{phase2}` to the
backtester. The matrix runner saw an empty symbols list (default `[]`),
iterated nothing, finished in ~38 seconds, and wrote zero rows to
`backtest_cache.json` — the verifier then approved nothing. Manual
backtest worked because the IPC handler in `main.js` filled the full
config. v1.7.6 mirrors that build: full canonical 8-symbol list, every
TF the live scan uses, BOTH directions, and `backtest_days` from
settings. Expected runtime jumps from 38 s to 5–15 min, and the
verifier produces real approval counts.

### Strategist crash in ranging-regime path
v1.7.5's `score_symbol_ranging` did `len(rates.get("close") or []) < 30`
which raised `ValueError: The truth value of an array with more than one
element is ambiguous` because `get_rates` returns numpy arrays — `arr or
[]` triggers the truthiness check. Replaced with explicit `is None` +
length guards. Same fix audited across `detect_market_regime` and the
existing trending pipeline.

### detect_market_regime data-availability check
The v1.7.5 condition `not rates.get("close") is not None` was a typo
that worked by accident. Cleaned up to a clear `is None` + minimum-bar-
count check so we never hand stunted arrays to `compute_adx`.

## ✨ Features

### Structural TP picker
The single-TP path now walks every recent swing-high/low, liquidity
sweep, BOS target, FVG, and order block in priority order
(liquidity > BOS > FVG > OB) and picks the **nearest** level past
`min_rr × SL`. The selected price is then pulled back by
`tp_structural_buffer_pips` (default 3) so close prints don't slide
right past the level. Three new settings on Order Execution → Take-
Profit Placement:

- **Place TP at structural level** (default ON) — toggles the picker.
  When OFF, falls back to the legacy RR-multiple TP.
- **Require structural TP at Min RR** (default OFF) — when ON, signals
  whose nearest structural target falls short of Min RR are REJECTED
  with reason `"RR 2:1 not reached at any structural level (swing /
  liquidity / BOS / FVG / OB) past entry"` rather than placing a pure
  RR-multiple TP. Filters out marginal setups; expect fewer trades but
  higher edge.
- **TP Pullback Buffer (pips)** (default 3) — how many pips inside the
  level the TP lands.

### Hardened mean-reversion strategy
v1.7.5's BB-touch entry was a knife-catch — bare M5 close beyond the
band, TP at mid (sub-1:1 RR), no higher-TF guard. v1.7.6 adds four real
filters:

1. **M15** instead of M5 — less wick noise.
2. **Wick rejection** — the previous closed bar must poke beyond the
   band AND close back inside. A continuation bar beyond the band no
   longer fires.
3. **Confirmation candle** — the most recent close must confirm the
   rejection direction (cur_close > prev_close for BUY).
4. **Higher-TF ranging guard** — H1 ADX must NOT be trending. If H1
   ADX ≥ `adx_trending_threshold` the signal is dropped.

SL anchors on the rejection wick + 5 pips (instead of band edge), TP
extends past mid into the opposite half of the band, and the setup is
silently dropped if RR < 1.5. Each skip path emits a clear `notes`
line so the dashboard / Engine Log can show exactly why a setup didn't
fire.

### Login / Register UX simplified
- Removed the Confirm Password field. The login form is now a single
  Email + Password pair regardless of whether a local password exists.
- First-time users: the typed password is silently saved as the local
  password — no separate "Create Account" step.
- New "Register on website" link opens
  `https://profitenginefx.onrender.com/#pricing` in the user's default
  browser via a new `window.api.shell.openExternal` IPC bridge (URL
  scheme is locked to http(s) so a renderer-side compromise can't open
  arbitrary protocols).

### Auto-reset on every launch
License-cache freshness was unreliable in v1.7.5 — boot-time
`license:check` passed but the engine's runtime validation rejected the
same token, manifesting as "License failed" the moment the user
pressed Auto Trading or Start Single Analysis. Manually clicking
Reset App fixed it, but only until the next launch. v1.7.6 wipes
`auth.json` + `license.json` + `.bak` + `lock` automatically on every
app launch so every run starts with a fresh server-validated license
and a re-authenticated session. Intended to be paired with auto-fill
license workflows; users with manual license entry will need to
re-paste their key on every launch.

## 🗂 Resources

### Bundled baseline three-file set
The installer now ships all three baseline artefacts in
`engine/agents/`:

- `baseline_bars_archive.db` (~24 MB, 280 K bars across 8 symbols × 4 TFs)
- `baseline_backtest_cache.json` (was missing in v1.7.5 ship)
- `baseline_manifest.json` (was missing in v1.7.5 ship)

The cache + manifest are what enables the verifier's WR-blend on new
installs — without them, fresh users had to wait their first Auto
Daily Update before the verifier could approve anything.

## Files touched

- `engine/trading_engine.py` — auto-update config fix, new auto-reset
  hook is in `main.js` not here
- `engine/agents/strategist.py` — numpy hotfix, regime-detect cleanup,
  hardened `score_symbol_ranging`, structural TP picker
- `engine/agents/baseline_bars_archive.db` + cache + manifest — full
  three-file set
- `renderer/src/pages/LoginScreen.jsx` — single-form login + "Register
  on website" link
- `renderer/src/pages/Settings.jsx` — Take-Profit Placement section
- `main.js` — auto-reset on app boot, `shell:openExternal` IPC handler
- `main/preload.js` — exposes `window.api.shell.openExternal`
- `package.json` — version 1.7.6

## Upgrade notes

No settings migration required. New keys (`tp_use_structural`,
`tp_require_structural`, `tp_structural_buffer_pips`) all default to
safe values. Mean-reversion users who tuned `ranging_strategy`
specifically should re-test — the new wick-rejection logic fires far
less often (single rejection bars, not every band touch) so signal
volume in chop markets drops noticeably.

The auto-reset on launch wipes any locally cached login session — make
sure you have a license auto-fill setup or be ready to re-paste the
license key each launch.

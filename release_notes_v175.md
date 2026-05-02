# ProfitEngineFX v1.7.5

Released: May 2026 — six functional enhancements: bundled baseline data,
ADX market-regime detection, simplified verifier, news-driven pending
cancellation, layered order modes (pyramid / grid / iceberg), and a
hardened risk-mode pill toggle.

## Highlights

### Bundled baseline + daily blend
The installer now ships with `engine/agents/baseline_bars_archive.db` —
a pre-built SQLite archive (~28 MB at release time) covering the canonical
8 symbols × 4 timeframes (M5 / M15 / H1 / H4). On first run the engine
copies the bundle into `%APPDATA%\ProfitEngineFX\bars_archive.db` if the
user's archive is empty, and an initial verifier run fires before the
first scan. The verifier blends bundled WR with the user's accumulating
backtest results trade-count-weighted, so freshly-installed users get a
fair edge estimate from day one rather than waiting for their broker
history to accumulate. Live trade results never feed back into WR — only
backtest simulation does, so the blend stays honest.

### Verifier simplification — WR + P&L only
The pre-1.7.5 verifier ran a five-gate gauntlet (WR, trades, score, RR,
worst streak) before the P&L gate. That hid real edge on small datasets:
a 65% WR / 30-trade combo with positive P&L would fail `min_trades >= 50`
and never reach the approved list. v1.7.5 strips four of the gates. The
verifier now only enforces:

- Min Win Rate (default 60%)
- Min P&L (% of balance or absolute USD, default disabled)

Min Trades / Min R:R / Max Worst Streak are no longer consulted. Min
Score moved to **Order Execution → Live Signal Score Floor** because it
gates live confluence, not backtest combos. Removed UI in the Agent
Verifier tab; the on-disk settings remain for downgrade compatibility.

### News-driven pending cancellation
A new **Sessions → News Cancel-Pending** toggle (default ON) sweeps every
EA-placed pending order on currency-affected symbols a configurable lead
time before each HIGH-impact news release (default 60 minutes). Operates
independently of the existing Tier-3 telegram alert path — works without
any telegram credentials configured, and dedupes per-(event, symbol) so
each event fires exactly one cancel wave. Cancels are logged as
`NEWS_CANCEL: <symbol> ticket=<n> event='<title>' in <Nmin>min` and
emitted as a Telegram summary if credentials are set.

### Layering modes — pyramid / grid / iceberg
A new **Layering** tab lets you scale the single-order default into a
stack of related orders. One mode at a time:

- **Pyramid** — primary fills, then `pyramid_levels − 1` buy/sell stop
  pendings staggered `pyramid_step_atr × ATR(M15)` apart in the trend
  direction with `pyramid_lot_decay` lot decay per leg. For runaway
  trends.
- **Grid** — `grid_layers` sell-limits above and `grid_layers` buy-limits
  below the primary, spaced `grid_spacing_atr × ATR(M15)` apart. Total
  lot capped by `grid_max_total_lot`. For ranging markets.
- **Iceberg** — primary lot replicated across `iceberg_slices` pendings
  spaced `iceberg_spread_pips` pips apart in the trade direction. For
  averaging slippage on volatile, low-liquidity symbols.

Default `layering_mode = "off"` — single-order behaviour matches v1.7.4
exactly. SL / TP / Multi-TP are inherited from the primary on every leg.

### Market-regime detection (ADX)
A new **Order Execution → Market Regime Detection** section enables
Wilder ADX on each symbol's H1 chart every scan. ADX > trending threshold
(default 25) → existing ICT-OB + BG + BOS + FVG continuation pipeline.
ADX < ranging threshold (default 20) → swap in a Bollinger ±2σ
mean-reversion strategy on M5 with halved risk and a 4-pip buffer past
the band edge. The grey zone (20–25) defaults to trending so a borderline
reading never silently re-routes. Each scan emits a
`REGIME_DEBUG: <symbol> <tf> ADX=<n> → trending|ranging|uncertain` log
line so the routing is auditable. ADX is cached for 60 seconds per symbol
to avoid hammering MT5.

### Risk-mode pill toggle hardened
The Risk Management and Verifier P&L `% of balance / $ Absolute USD`
pills now resolve mode strictly. Anything other than the two valid string
values (e.g. an undefined or stale key in `settings.json`) is treated as
`'percent'` and backfilled at load time, so the active pill always
matches persisted state from page load — fixes the long-standing report
that the toggle "didn't stick" on a freshly-installed settings.json.

## Files touched

- `engine/trading_engine.py` — baseline-copy seed (carried over from
  v1.7.4), `_run_verifier` simplified to WR + P&L, new
  `_news_cancel_pending_tick`, `_apply_layering` router with three mode
  implementations, new layering / regime / news-cancel keys in
  `DEFAULT_SETTINGS`.
- `engine/agents/strategist.py` — new `compute_adx`, `detect_market_regime`,
  `score_symbol_ranging` (Bollinger mean-reversion); `score_symbol`
  routed through regime detection when enabled.
- `engine/agents/baseline_bars_archive.db` — bundled SQLite archive
  (~28 MB at release).
- `tools/export_baseline.py` — already shipped in v1.7.4; rerun by P
  before this build to refresh the bundled archive.
- `renderer/src/pages/Settings.jsx` — new TabLayering, regime settings
  in TabExecution, Min Score moved out of TabVerifier, news-cancel
  controls in TabSessions, defensive backfill for the four pill modes.
- `package.json` — version 1.7.5.
- `publish-1.7.5.ps1` — full publish automation (vite → engine →
  electron-builder → installer rename → index.html bump → git push →
  gh release).

## Upgrade notes

No settings migration required. New keys (`layering_mode`,
`regime_detection_enabled`, `news_cancel_pending_enabled`, ranging-
strategy params, etc.) all default to safe / opt-in values that preserve
v1.7.4 behaviour out of the box. The verifier's removed thresholds
(`verifier_min_trades`, `verifier_min_rr`, `verifier_max_worst_streak`)
are still written to disk but ignored — you can downgrade to v1.7.4
without losing them.

The bundled baseline archive only seeds the user's archive when their
local `bars_archive.db` is missing or empty — long-running users keep
their accumulated history untouched.

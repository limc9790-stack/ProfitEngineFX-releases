# ProfitEngineFX v1.9.17 — Production-Tuned Defaults

Released: May 2026

## Why this release

v1.9.16 introduced per-symbol safety caps but left `risk_per_trade_percent`,
`max_lot_override`, and the three counter-trend filters (`htf_trend_filter`,
`require_trigger_candle`, `counter_wick_guard_enabled`) as user-tunable knobs
that ship OFF or at lenient defaults. Live trading on v1.9.16 over a 1-month
window on a $25k Funding Pips account converged on a tighter set of values
than the v1.9.16 ship defaults — and every new user was landing on the
lenient defaults until they tuned them by hand.

v1.9.17 makes the live-tested values the new floor. Fresh installs land on
P's exact production config. Existing users get the safety caps force-applied
on upgrade (lower of user-or-v1.9.17 wins) while credentials, broker config,
and enabled symbols are preserved.

## What changed

### 🔴 Critical — production-tuned safety caps baked in

1. **Per-symbol lot ceilings tightened ~3x.** Every cap in
   `max_lot_override` derives from "worst-case SL hit on a $25k account
   lands at 1-2% of equity." BTC: 1.0 → **0.3**. ETH: 2.0 → **0.5**. XAU /
   XAG: 2.0 → **0.5**. EUR / USDJPY / GBPUSD / AUDUSD: 2.0 → **0.5**. GBPJPY
   / EURJPY: 1.5 → **0.3** (lesson from the 2026-05-14 -$814 loss). NDX100 /
   SPX500 / DJI30 / US30 / UK100 / GER40: 0.5 → **0.1** (high $/pt). The
   `max_lot_override_enforced` flag is force-set true on upgrade so the
   ceilings actually apply.

2. **`risk_per_trade_percent` hard-capped at 2% on upgrade.** v1.9.16
   soft-capped users who had 3% or higher; v1.9.17 takes `min(user, 2)` so
   anyone running 2.5% gets clamped too. Logs
   `MIGRATION_V1917 risk_per_trade_percent capped <X> -> 2`. The user can
   raise it back in Settings — we cap on upgrade as a one-time guardrail.

3. **Three-layer daily-loss protection.** `max_daily_losses: 3` stops the
   bot after 3 closed losing trades today. `risk.loss_breaker` was
   3-consecutive → 1-hour pause; now `max_consecutive_losses: 1` and
   `pause_hours: 24` — one loss triggers a 24-hour cooldown.
   `risk.daily_drawdown.max_daily_loss_pct: 3` with `hard_stop: true` flips
   `auto_trading=False` the instant today's account drawdown hits 3%.
   Combined, this is a belt-and-braces revenge-trade guard.

### 🟡 Counter-trend protection force-enabled

4. **`htf_trend_filter`, `require_trigger_candle`,
   `counter_wick_guard_enabled` all force-on.** In v1.9.16 these defaulted
   OFF, leaving entries vulnerable to counter-trend stabs and falling-knife
   fills. v1.9.17 forces them all true on upgrade and mirrors
   `strategy.htf_filter.enabled = true` so legacy and current code paths
   stay in sync. `htf_timeframe` lowered H4 → **H1** (more responsive).
   `counter_wick_min_pct: 0.4` requires a 40% counter-wick before the entry
   is blocked.

5. **Multi-TP auto-BE after TP1.** `multi_tp_be_after_tp1: true` is now the
   default. The existing 33/33/34 ladder at RR 1/2/3 fires TP1, then
   immediately moves SL to entry on the remaining two slices.

### 🟢 Migration safety net

6. **Safer-wins merge on per-symbol caps.** The migration takes
   `min(user_cap, v1917_cap)` per symbol — if a user had GBPJPY=0.2
   (already safer than v1.9.17's 0.3) it stays 0.2. If they had BTC=2.0
   (riskier) it tightens to 0.3. Custom symbols the user added (not in the
   v1.9.17 default set) are preserved untouched.

7. **`symbol_map` broker-alias repair.** Some pre-v1.9.15 configs ship with
   `NDX100→NAS100`, `SPX500→US500`, or `DJI30→US30` (broker aliases that
   most MT5 brokers don't carry, breaking lot lookup). The migration
   repairs each to identity mapping. Custom user mappings on other symbols
   are preserved (`symbol_map` is in `PROTECTED_USER_FIELDS`).

### 🧊 Carryover guards — unchanged from v1.9.16

8. **Per-symbol MR profile table.** `DEFAULT_MR_PER_SYMBOL_V1917` is an
   alias to V1916's table — no MR tuning changes between v1.9.16 and
   v1.9.17. The migration still backfills `min_wr` for any custom per-
   symbol entry the user added.

## Files touched

- `engine/trading_engine.py` — `DEFAULT_SETTINGS_V1917` dict
  (production-tuned values), `DEFAULT_MR_PER_SYMBOL_V1917` alias,
  `_merge_v1917_into_defaults()` helper for the global DEFAULT_SETTINGS
  splice, `CONFIG_SCHEMA_VERSION_V1917 = 1917`, `_run_v1917_migration()`
  (force-cap risk at 2, safer-wins merge on `max_lot_override`, symbol_map
  repair, force-on filters), migration chain wire-up after
  `_run_v1916_migration`.
- `package.json` — bumped 1.9.16 → 1.9.17.
- `build_v1917.ps1` — NEW. Adapts `build_v1916.ps1` with 15 v1.9.17 sanity
  assertions (schema bump, override caps tightened, safer-wins behavior,
  symbol_map repair, force-on filters, credential preservation) before
  Nuitka / Vite / electron-builder run.

No new code paths. No new UI controls. Pure default-tuning + migration build.

## Upgrading

Standard `ProfitEngineFX-Setup-1.9.17.exe` over the previous install. The
migration runs once on first launch, auto-applies the new safety caps, and
bumps `config_schema_version` to 1917. Re-launching is a no-op (idempotent).
A pre-migration backup is saved at
`settings.json.bak.pre-migration.<timestamp>` (last 10 retained) for rollback.

Preserved through the migration: `telegram_bot_token`, `telegram_chat_id`,
`mt5_login`, `mt5_password`, `mt5_server`, `mt5_path`, `finnhub_api_key`,
`license_key`, `user_email`, `enabled_symbols`, `enabled_tf_configs`,
`symbol_map` (custom mappings preserved; only broken
NAS100/US500/US30→internal aliases repaired), session toggles,
`auto_trading`, `scan_interval_min`, your `min_wr` per-symbol overrides.

Force-applied on upgrade: `risk_per_trade_percent` capped at 2,
`max_lot_override` per-symbol `min(user, v1.9.17 ceiling)`,
`max_lot_override_enforced=true`, `htf_trend_filter`,
`require_trigger_candle`, `counter_wick_guard_enabled`, all three force-set
true.

## Verifying the fixes

After upgrade, in `trading_engine.log` watch for:

- `ENGINE_START v1.9.17` — confirms the new build is running.
- `CONFIG_MIGRATION_V1917_APPLIED: production-tuned defaults baked | ... risk_pct=<X> (was <Y>) | override_enforced=True | htf_filter=True (was <bool>) | trigger_candle=True (was <bool>) | counter_wick=True (was <bool>) | max_daily_losses=3` — one-shot audit of the migration's effect.
- `MIGRATION_V1917 risk_per_trade_percent capped <X> -> 2` — fires only if your prior `risk_per_trade_percent` was above 2.
- `MIGRATION_V1917 max_lot_override: N caps applied, M user caps tightened to v1.9.17 ceilings, enforced=True` — N is the total entries in the merged override dict; M is how many user caps were above the v1.9.17 ceiling.
- `MIGRATION_V1917 symbol_map[NDX100]: NAS100 -> NDX100` (and SPX500/DJI30 variants) — fires only if your `symbol_map` shipped with broken broker aliases.
- `SAFETY_SUMMARY v1.9.17 caps: BTC=0.3 ETH=0.5 XAU=0.5 GBPJPY=0.3 NDX100=0.1 SPX500=0.1 DJI30=0.1 | loss_breaker max_consec=1 pause_h=24` — one-shot dump of the active caps right after migration.
- `SAFETY_SUMMARY schema=1917 risk_per_trade_pct=1 ...` and `SAFETY_CAP <SYM>=<value>` lines — emitted at every engine startup so you can confirm the v1.9.17 caps are still in force.
- `MIGRATION_V1917_INTEGRITY_FAIL key=<X> ... — restored` — should never fire in a clean upgrade; if it does, the credential/protected-field integrity check caught a regression and rolled the value back from the pre-migration snapshot.

Re-launch the engine after the first upgrade — `CONFIG_MIGRATION_V1917_APPLIED` should NOT fire a second time. If it does, the schema gate is broken (open a bug).

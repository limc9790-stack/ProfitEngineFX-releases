# v1.7.1 — Bypass Verifier + Better Error Messages + Wider SL

## What's new

- **Bypass verifier approval** (new setting ypass_verifier_approval in settings.json) — let users with short broker history trade live signals without waiting for Verifier approval.
- **Better order failure messages** — when MT5 returns no result, the engine now logs mt5.last_error() so you can see the actual reason (TRADE_DISABLED, SYMBOL_NOT_SELECTED, etc.) instead of generic ORDER_FAILED.
- **Wider SL with OB+ATR buffer** (settings: `sl_use_ob_anchor`, `sl_atr_buffer`, `min_sl_buffer_pips`) — SL is placed past the order block plus an ATR-scaled cushion. Lot size auto-adjusts to keep the same dollar risk.
- **Backtest threading** — backtests now run in their own thread so break-even / multi-TP / position management keep working while a backtest is running.
- **Symbol mapping unification** — backtester always writes archive bars under the canonical name (NDX100, BTCUSD…) regardless of broker alias (USA100, #BTCUSD…), eliminating duplicate Historical Archive entries.

## Includes all v1.7.0 fixes

- Lot-clamp on broker minimum
- Auth path fix (FundingPips → ProfitEngineFX rebrand)
- Login screen focus recovery (Electron 28 IME bug)
- License backdate self-heal + better IPC error surfacing

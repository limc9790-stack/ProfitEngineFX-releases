# ProfitEngineFX v1.7.3

Released: $(today) — Iteration on v1.7.2's broker-comment fix with a multi-TP
upgrade for pending orders, structural-reason tagging across logs and
Telegram, and per-symbol break-even pip thresholds always-visible in the UI.

## Highlights

### Multi-TP now works on pending orders
Pending orders previously fell back to single-TP because the order ticket
returned by `mt5.order_send` is different from the position ticket created on
fill. v1.7.3 stores the multi-TP arming under the order ticket in
`pending_multi_tp.json` and promotes it to a position-keyed entry the first
tick after fill, matched by symbol + direction + entry price. Cancelled or
expired pending orders are auto-cleaned from the arming file.

### TP "reason" tagged everywhere
Each multi-TP target now carries a human-readable reason (Liquidity Pool /
Break of Structure / Fair Value Gap / Order Block / RR Fallback) computed by
the strategist and surfaced in:

- `APPROVE` scan log lines (`tps=[2025.50(Liquidity Pool),2032.00(Order Block),...]`)
- `MULTI_TP_ARMED` log on order placement
- `MULTI_TP_HIT` log on each slice fired
- New Telegram **🎯 Multi-TP Hit** alert showing TP slot, RR, lot closed, reason
- Updated **🛡️ Breakeven Set** Telegram when BE-after-TP1 fires (now shows
  the structural reason that triggered TP1)

### Break-even diagnostic logging
`_manage_breakeven` was previously silent when it skipped a position. v1.7.3
emits a `BE_SKIP` log line at every continue point with a clear reason
(no_sl_set / already_at_breakeven_buy / risk_distance_invalid /
usd_below_threshold / pips_threshold_missing_for_XAUUSD / rr_below_1:1 / etc).
SL-modify rejections from the broker now log `BE_MODIFY_REJECTED` with the
retcode, broker comment, and `mt5.last_error()` value — so the recurring
"BE didn't fire on XAUUSD at +$10" class of bug is finally legible.

### Per-symbol BE pip thresholds — always visible
The pip-threshold table for `breakeven_trigger_mode = 'pips'` is now shown in
the Settings → Break-Even tab regardless of the active trigger mode (with a
"configured but inactive" hint when not in pips mode). Previously the table
was only rendered when pips mode was selected, so users couldn't see or
configure thresholds ahead of switching modes.

### Mutual exclusion (Multi-TP ↔ Partial Close)
The Settings UI now enforces mutual exclusion in BOTH directions: turning on
Partial Close auto-disables Multi-TP, and turning on Multi-TP auto-disables
Partial Close. The engine-side defensive check (Multi-TP wins when both are
flagged) remains as a backstop.

### New: skip when lot would be clamped
Optional `skip_when_lot_clamped` setting (default OFF) — when ON, trades whose
risk-based lot computes below the broker's `volume_min` are SKIPPED instead of
clamped UP to broker min. Helpful on small accounts where clamping over-risks
the per-trade budget. Engine logs `LOT_CLAMP_SKIP` for visibility. Toggle
lives at Settings → Risk → Lot Clamp Behavior.

## Files touched

- `engine/trading_engine.py` — multi-TP for pending orders, BE diagnostic
  logging, BE_MODIFY_REJECTED, lot-clamp skip, pending → position promotion
- `engine/agents/strategist.py` — `reason` field on TP targets
- `engine/telegram_alerts.py` — new `notify_multi_tp_hit`
- `renderer/src/pages/Settings.jsx` — pip table always visible, mutual
  exclusion both directions, lot-clamp toggle UI
- `package.json` — version 1.7.3

## Upgrade notes

No settings migration required — new keys (`skip_when_lot_clamped`) default
to false to preserve v1.7.2 behavior. Existing `position_meta.json` entries
remain valid (the new `reason` field is optional and falls back to `source`).

A new sidefile `pending_multi_tp.json` is created in the user's data
directory the first time a pending order is placed with Multi-TP enabled.

## v1.6.1 — Tier mapping fix + auto-trading gate

### Server (auto-deployed via Render)
- Fixed: `/api/auth/login` now reads `licenses.plan` (billing source-of-truth) instead of `users_profile.tier`. This corrects all VIP / Trial / Signal users who were being mis-classified.
- Returns real `expires_at` and a `permanent` flag for never-expiring licenses (no more 365-day defaults).

### Desktop app
- Auto-trading is now correctly gated by tier: VIP and active Trial users get full features, Signal users get signals only.
- Engine itself enforces the tier gate (not just the UI), closing a security gap where a stale UI state could allow signal users to auto-trade.
- Trial expiry now downgrades automatically the moment expiry is reached, no relogin needed.
- Bug fix: partial close Telegram notifications now show the real realised P&L (was showing $0.00 due to reading position.profit before the deal settled).
- Bug fix: breakeven now fires reliably when partial close fires (was missing on fast price reversals).
- Bug fix: license refresh — engine now picks up new auth tokens within ~5 seconds without needing an app restart.

### Download
Windows: see assets below.

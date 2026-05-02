## v1.6.4 — Reliability + history fixes

### Startup license check
- **Fixed:** transient remote-time fetch failures at cold startup no longer kick the user to the login screen. Cached `license.json` is now treated as offline-OK at startup whenever the on-disk license is still valid (email present, expiry not yet reached). Only **terminal** rejection reasons (`expired`, `locked`, `no-license`, `needsActivation`, `backdate`) route the user to the License screen at startup. Network/error/unknown results fall back to the cached license. Auth mirror to `auth.json` runs on every offline-OK fallback so the engine's own check sees the same token without delay.

### Backtest history download
- **Fixed:** "Download 100 days of history" was reporting 0/32 succeeded even when MT5 itself had 100+ days available. The download anchor walk now issues an explicit `mt5.copy_rates_range(anchor, anchor+35d)` after each `copy_rates_from` nudge, which actually deposits bars into the local cache. Settle delays between steps doubled (broker delivery latency on M5 was the most common cause of false "insufficient" results).

### Rolling archive maintenance
- New: **auto-rolling 100-day archive**. Once per day at the configured SGT time (default 00:30), the engine triggers `Download History` which appends today's new bars and prunes anything older than `archive_retention_days` (default 100) — yielding a sliding 100-day window without manual user action. Settings: `archive_auto_rolling_enabled` (default `true`), `archive_rolling_time_sgt` (default `"00:30"`), independent of the existing Auto Daily Update so users can keep one without the other.

### Download
Windows: see assets below.

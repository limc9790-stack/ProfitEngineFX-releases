## v1.6.5 — Session refresh + history-download diagnostics

### Engine session-refresh
- **Fixed:** every cold launch was forcing "Reset App + re-login" because the engine crashed with `LICENSE_ERROR: Session expired` (exit 3) when both access and refresh tokens returned 401. The engine now emits `SESSION_REFRESH_NEEDED: {email, license_key, ts}` and exits cleanly with code 2. The renderer pops a small password-only modal (email pre-filled) — settings, license.json, MT5 connection, and open positions are all preserved. Successful re-auth writes fresh tokens to auth.json and re-spawns the engine.
- Dedup flag prevents duplicate signals if the path is hit more than once in a single launch.
- `LICENSE_EXPIRED_HARD` (real expiry past 3-strike grace) is unchanged — still routes to the full-screen "Please subscribe" page.

### History-download diagnostics
- **Added:** verbose `DOWNLOAD_DEBUG` lines for every `copy_rates_from`, `copy_rates_range`, `symbol_select`, and `symbol_info_tick` call during the "Download 100 days" flow. Each line includes the broker symbol, timeframe, anchor / window, bars returned, and `mt5.last_error()`. Surfaces the actual MT5 error code so we can finally tell whether the broker is rate-limiting, the symbol isn't in Market Watch, the date range is past the broker's depth cap, or the engine is being interrupted mid-loop. Run "Download History" once and the answer will be in `engine_crash.log`.

### Download
Windows: see assets below.

## v1.6.6 — Three production fixes

### Backtest history fetcher (download path B)
- **Fixed:** the backtest history fetcher (`_fetch_bars` in `backtester.py`) was on a different code path than the green "Download 100 days of history" button. The fetcher's `copy_rates_range` and `copy_rates_from(far_past, 999_999)` attempts repeatedly returned 0 bars on FundingPips for **XAUUSD, EURUSD, GBPJPY, NDX100, SPX500**. The fetcher now uses the same **backward-walking 5000-bar chunk loop** the Download button has used successfully since v1.6.5: walk `copy_rates_from(anchor, 5000)` from `now` backward, advance the anchor to one bar before the oldest each iteration, repeat until target collected (cap 50 hops). Successful fetches still merge into the persistent archive.

### Startup license check
- **Fixed:** even with v1.6.4's offline fallback, users were still being routed to the License screen on cold launches. The `verifyWithServer()` post-validate call was treating any `valid:false` response (including transient server hiccups) as a terminal "device mismatch" and forcing re-registration. The check is now strict — only an EXPLICIT terminal reason (`device-mismatch`, `revoked`, `expired`, `no-license`, `needsActivation`) routes to the License screen. Transient server failures keep the user on the local cache.

### Login form focus
- **Fixed:** post-Reset-App login screen sometimes dropped the first keystrokes until the user clicked outside the window and back. Added a third focus retry at 400ms with a documented Electron `window.blur(); window.focus();` workaround that forces the OS-level input-method context to re-bind to the new window.

### Download
Windows: see assets below.

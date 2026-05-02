## v1.6.7 — "Download 100 days of history" button actually works

- **Critical fix:** the green "Download 100 days of history" button on the Backtest page has been a **no-op since v1.1.7**. The button sent `DOWNLOAD_HISTORY` over stdin to the engine, the engine set `self._download_history_requested = True`, **but nothing in the main loop ever consumed that flag**. So clicking the button just toggled an in-memory boolean that no code path ever read. The successful downloads users saw at scheduled times came from the auto-rolling scheduler (added in v1.6.4), which calls `_handle_download_history()` directly — masking the bug.
- The main loop now consumes the flag every tick and runs `_handle_download_history()` (the proven backward-walking 5000-bar chunk loop). The button finally does what its label says.
- Carried over from v1.6.6 (in case the previous build artifacts were incomplete): backward-walking fetcher in `backtester._fetch_bars`, strict-terminal-only `verifyWithServer` check at startup, login form focus retries with `window.blur(); window.focus();` workaround.

### Download
Windows: see assets below.

## v1.7.0 — Lot-clamp + auth path + login focus + license self-heal

Four fixes that resolve user-visible bugs in v1.6.x and avoid silent order rejection on prop-firm broker accounts.

### Fixed

- **Lot-min clamp on order placement.** `_execute_smart_order` now consults the broker's actual `volume_min`, `volume_step`, and `volume_max` from `mt5.symbol_info` when sizing the order. The previous hardcoded `0.01` floor + 2-decimal rounding caused MT5 retcode `10014 INVALID_VOLUME` rejections on brokers where XAUUSD / indices / crypto have `volume_min ≠ 0.01` (common on prop-firm and ECN accounts). When the computed lot falls below `volume_min`, it is clamped UP and a `LOT_CLAMP` line is logged. Also resolves the `order_failed` symptom users hit after lowering risk-per-trade from 1% to 0.5%.

- **Specific failure reason in scan output.** Scan output now reports the real failure cause (`INVALID_VOLUME`, `MARKET_CLOSED`, `REQUOTE`, `NO_MONEY`, `TRADING_WINDOW_CLOSED`, `PORTFOLIO_RISK_REJECT`, etc.) instead of bucketing every rejection under the generic `order_failed`. MT5 retcodes are mapped to short uppercase mnemonics in the engine.

- **Auth-path mismatch.** `main/api-client.js` was reading and writing `auth.json` and `settings.json` under `%APPDATA%\FundingPips\` (a leftover from the FundingPips → ProfitEngineFX rebrand), while everything else used `%APPDATA%\ProfitEngineFX\`. The mismatch left every api-client request token-less, surfacing as a generic "license failed" error after a successful login. The api-client now uses `app.getPath('userData')` and shares the same directory as the rest of the app.

- **Login screen focus.** `LicenseScreen.jsx` had no focus management, so on Electron 28 cold launches and post-Reset-App reloads the first keystroke into the email or password input was dropped — users had to click outside the field and back to make it accept input. Ported the multi-attempt focus-recovery hook from `LoginScreen.jsx` (rAF + 120 ms + 400 ms retry, `window.blur()/focus()` workaround, one-shot `'focus'` listener) and attached it to both the Login and Register tabs. The email field is no longer `readOnly` when locked — users can correct it without first clicking "Change". The visual lock indicator stays.

- **License backdate self-heal.** `validateOnLaunch` now compares the system clock against the build's release timestamp before locking on a backdate-detection hit. If the OS clock is plausibly correct (≥ release − 10 min and ≤ release + 2 years), the floor is reset and the user continues normally with a clear breadcrumb logged to `engine_crash.log`. Previous behaviour locked the install permanently and forced a full Reset App when an older buggy build had poisoned `last_known_time_iso` into the future.

- **License IPC error surfacing.** `license:check` and `license:status` now return a normalized payload that always includes `reason`, `message`, and `errorCode` fields, so the renderer can show specific errors ("License expired", "Could not validate license — check your connection", "System clock issue — contact admin") rather than a generic "license failed".

- **Reset App.** Now also wipes `license.json.bak` (last-known-good copy) and `license.lock` in addition to `auth.json` and `license.json`, so a backdate-locked install actually returns to a clean state.

### Notes

Bumping risk-per-trade from 1% to 0.5% on a small account no longer causes order rejections. Be aware that on accounts where the computed lot falls below `volume_min`, the trade will use slightly more than the configured 0.5% risk because we clamp UP to the broker minimum — this is the documented trade-off.

### Download
Windows: see assets below.

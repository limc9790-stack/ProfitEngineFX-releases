## v1.6.8 — Truly silent license re-auth

- **New backend endpoint** `POST /api/auth/silent-refresh` (server-side, deployed to Render). Accepts `{ email, license_key, machine_id }`, validates against the `licenses` row (user lookup, license existence, expiry, key match, device binding), and mints a fresh Supabase session via the admin `generate_link → verify_otp` pattern. Returns `{ access_token, refresh_token, expires_at }` on success or 401 with a structured `reason` (`no-user` / `no-license` / `expired` / `wrong-key` / `device-mismatch`).
- **Engine** (`trading_engine.py`) now includes the real `license_key` in the `SESSION_REFRESH_NEEDED` payload — falls back to reading `license.json` when `auth.json` doesn't carry the key (older logins).
- **Renderer** (`App.jsx`) now does silent re-auth on `SESSION_REFRESH_NEEDED`: POSTs to `/api/auth/silent-refresh`, persists fresh tokens to `auth.json`, and re-spawns the engine. **The user sees nothing.** Terminal 401 reasons (`expired`, `no-license`, `wrong-key`, `device-mismatch`) route to the License Expired full-screen page. Network / 5xx / `transient` errors retry once after 30 s and otherwise leave state alone — never bothers the user.
- The password-only session-refresh modal from v1.6.5 is removed.

### Download
Windows: see assets below.

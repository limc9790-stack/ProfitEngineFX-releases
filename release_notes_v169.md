## v1.6.9 — Download success-counter fix

- **Fixed:** "Download 100 days of history" was reporting `0/32 succeeded` even when the persistent archive already had 100+ days of data. The success criterion was based on `bars_fetched_this_run vs expected`, which on incremental updates is always small (the archive already had everything; only a few new bars to add). The criterion now uses **`archive_days_after >= window_days × 0.95`** — what's actually in the archive after the merge — which is the right question to ask.

### Download
Windows: see assets below.

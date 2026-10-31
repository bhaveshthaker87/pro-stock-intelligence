# Automated NSE EOD history

The scheduled workflow `.github/workflows/nse-eod-ingestion.yml` checks the official NSE All Reports page after the cash-market close, discovers a matching CM-UDiFF Common Bhavcopy Final ZIP link, downloads it over HTTPS, validates it with the existing UDiFF parser, and persists one immutable CSV plus metadata JSON per trading date under `data/nse/eod/`.

- `YYYY-MM-DD.csv`: EQ-series OHLCV bars. Every row is labelled `marketDataStatus=EOD`.
- `YYYY-MM-DD.json`: source URL, NSE trading date, UTC fetch time, row count and source ZIP SHA-256.
- `index.json`: durable manifest of all retained trading dates.

The ingestion fails closed if NSE does not expose a matching official HTTPS link, the ZIP is malformed, row dates do not match the filename, or an existing daily file would be overwritten with different data. The workflow runs on weekdays at 14:30 UTC (20:00 IST) and can also be run manually.

## Important limits

This workflow persists validated stock EQ EOD history in Git. It does not create live quotes or intraday candles. The first successful scheduled/manual run against a real NSE report is still required to validate NSE's current HTML/link behavior and the live report payload. Unit tests use synthetic fixtures and do not count as a real-feed reconciliation.

Index history, corporate actions, announcements and financial results are separate datasets and are not produced by this stock-bhavcopy workflow. Screener is not accessed or scraped by this job.

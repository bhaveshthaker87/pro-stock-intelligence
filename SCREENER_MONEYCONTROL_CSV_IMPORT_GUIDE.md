# Authorized CSV import guide (V40.72)

## Screener.in
1. Sign in to Screener.in and run the stock screen you need.
2. Use **Edit columns** to add the metrics you want in the export (Screener documents up to 50 columns for Premium).
3. Export the screen as CSV.
4. In Pro Stock Intelligence choose **Data Sources / CSV → Screener.in CSV export** and select the file.

The import maps recognized headers such as NSE Code, Current Price, Market Capitalization, Stock P/E, EPS in Rs, ROCE, ROE, Debt to equity, Dividend yield, Book value, and selected growth/ownership fields. Unknown fields are skipped; no fuzzy company-name matching is used. To cover a wide range of stocks, include NSE Code in the export.

## Moneycontrol
Select **Moneycontrol CSV export** only if your account/product offers a CSV export and its terms permit the intended use. A subscription login by itself does not grant permission for automated extraction into a database. This app does not scrape Moneycontrol or use your login credentials. If no permitted export is offered, use the official website for manual research or obtain an authorized data feed/API and written permission.

## Historical chart CSV
The importer also recognizes OHLCV CSV headers such as Date, Open, High, Low, Close, Volume. Select the stock in the app before importing a single-stock history file. At least 20 valid bars are recommended; the app sorts dates, rejects malformed OHLC rows, and labels the result as user-imported—not exchange-certified.

## Data safety
- CSV import is local to this WebView; imported data is not a live provider feed.
- The app fills only missing fundamental fields when the checkbox is enabled; live values take precedence. Conflicts are surfaced.
- Reporting period/as-of time are not inferred when absent from the export. Verify period and freshness before relying on imported values.
- Remove imported data from the same dialog.


## V40.72 provider-status note

The app now exposes a provider diagnostics panel. It can detect the presence of a Screener session cookie, but only a successful protected company-page request validates that session. Moneycontrol public stock pages can be opened without login; the app does not automatically extract data from them. Automated Moneycontrol ingestion remains disabled until an authorized documented feed/API or written permission is configured.

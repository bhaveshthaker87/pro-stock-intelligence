# NSE public EOD file import

The app's selected market-data policy is **public NSE end-of-day files only**. Do not use unofficial quote endpoints, third-party quote fallbacks, or call an EOD close a live quote.

## Official source and format

Use NSE's **All Reports → Equities → CM-UDiFF Common Bhavcopy Final (zip)** report. NSE states the older CM Bhavcopy CSV and Common Bhavcopy CSV reports were discontinued from 8 July 2024; use the UDiFF ZIP instead.

Official report page: https://www.nseindia.com/all-reports

The UDiFF cash-market CSV includes fields such as `TradDt`, `TckrSymb`, `SctySrs`, `OpnPric`, `HghPric`, `LwPric`, `ClsPric`, and `TtlTradgVol`. This converter keeps only `EQ` series and validates prices, OHLC consistency, duplicate symbol/date rows, and date values.

## Convert a downloaded NSE ZIP

```sh
python3 tools/convert_nse_udiff_bhavcopy.py /path/to/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip -o nse_eod_import.csv
```

Then import the normalized CSV using **Data Sources / CSV** in the app, choosing **Other authorized CSV**. Keep the generated source and date columns with the imported file. The import is a historical EOD snapshot; it does not create live quotes or intraday candles.

## Output contract

Each row includes `symbol,date,open,high,low,close,volume,source,marketDataStatus`. The status is always `EOD`; the source is `NSE CM-UDiFF Common Bhavcopy Final`. The date is the exchange trading date, not the file download time.

## Limits / verification

- This converter does not download data automatically; download the report from the official NSE page.
- This first implementation covers NSE cash-market `EQ` bars only, not indices, derivatives, corporate actions, or financial results.
- A successful parse proves file structure and row validation, not independent accuracy of every security record.
- A real downloaded report should be retained with its date for reconciliation before claiming production data validation.
- Screener fundamentals remain unavailable until a genuine authorized export or verified session is supplied; no third-party source is substituted.

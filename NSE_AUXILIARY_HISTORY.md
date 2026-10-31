# Separate NSE index and corporate-history ingestion

This importer deliberately keeps the sources separate from equity-security bhavcopy.

## Index history

Download the historical index CSV from the official NSE Historical Index Data page or NSE Indices Historical Data reports. Import it with:

```sh
python3 tools/ingest_nse_auxiliary_history.py indices official-index-history.csv \
  --source-url 'https://www.niftyindices.com/reports/historical-data' \
  --output-dir data/nse/indices
```

It validates index name, date, OHLC columns, duplicates and OHLC consistency, then writes one EOD JSON file per date and a provenance manifest. Index rows are never derived from equity stock bhavcopy.

## Announcements, corporate actions and board meetings

NSE's Market Activity Reports documentation describes `nuprddmmyy.zip` contents:
- `Anddmmyy.txt`: announcements
- `Bcddmmyy.csv`: corporate actions
- `Bmddmmyy.txt`: board meetings

Download the official archive from NSE and import it:

```sh
python3 tools/ingest_nse_auxiliary_history.py corporate nupr311026.zip \
  --source-url 'https://www.nseindia.com/all-reports' \
  --output-dir data/nse/corporate
```

The importer retains those original files by category and exchange date, with file hashes and provenance. It does not guess undocumented field delimiters or manufacture normalized event descriptions. A separate schema adapter and independent sample validation are still required before these raw records can be shown as structured events in the app.

## Limits

These are authorized-file import paths, not autonomous download schedulers. The caller must obtain the file directly from the official site and supply its official URL. Financial results / company filings are not parsed by this archive importer; they require their own official filing export schema and should not be inferred from board-meeting or announcement text. All records are EOD/historical, not live.

# How to use your own data

```powershell
py trader.py --mode csv --prices .\my-prices.csv --output .\output-custom
```

CSV header: date,symbol,close. ISO dates (YYYY-MM-DD), positive finite close prices,
at least six observations per symbol, one row per symbol/date. Rows are sorted internally.
Use legally obtained, consistently adjusted historical data; no data service is included.
No freshness or corporate-action checks are performed. The bundled DEMO symbol is invented.

Research gives historical period change and a five-observation moving-average paper simulation.
Each symbol gets its own independent 10,000 virtual cash account. It is not a combined portfolio.
At most 20% of current cash is allocated when entering; whole shares, no borrowing or shorting.
Signal: previous close above previous five-close mean. Fill: next observation's close.
Exit when signal is false. Default fee 10 basis points on each side; --fee-bps changes this.
Cash and equity are simulated in the input price's currency; do not mix currencies for comparisons.
Reports overwrite the selected output folder's research files; no persistent trading ledger.
No broker SDK, API, credentials, network requests or real-trade mode exists.
These are educational historical calculations, not investment recommendations or profit promises.

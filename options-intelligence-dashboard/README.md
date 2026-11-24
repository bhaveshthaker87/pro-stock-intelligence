# Options Intelligence — Independent Dashboard

This directory is a standalone browser dashboard. It is separate from the PRO STOCK INTELLIGENCE Android application: it does not modify, import, embed, or depend on Android app code.

## Run
Open \`index.html\` in a modern browser. No build step or local server is required for the current static prototype.

## Included
- Independent overview and data-validation workspaces
- CSV option-chain import and structural validation (imported rows are not authenticated)
- Black–Scholes theoretical price and Greeks calculator
- Multi-leg option strategy builder with expiry payoff chart
- Position risk-budget calculator
- Historical options backtesting requirements and validation protocol
- Local audit log and CSV export

## Data and safety boundaries
- No live NSE/broker API is connected.
- Example chain rows are synthetic and clearly labelled.
- Imported CSV data is not certified as exchange-originated.
- No order placement, broker authentication, or automated BUY/SELL signal is implemented.
- No historical backtest performance is claimed.
- Provider credentials must be held server-side when an authorized feed is later integrated; never place API secrets in browser JavaScript.

## Production work still required
1. Confirm authorized provider and permitted usage.
2. Build a server-side adapter for timestamped underlying quotes, option chain, contract master and historical options.
3. Validate source timestamps, contract identity, bid/ask, IV, OI and volume.
4. Add independent Greeks parity tests.
5. Implement point-in-time historical backtests with realistic spreads, slippage, costs, expiry and lot-size changes.
6. Add walk-forward and untouched out-of-sample validation.
7. Establish prospective paper-trading thresholds before any live decision workflow.

# V43.11 Options Intelligence Foundation — implementation boundary

## Included in this increment
- Adds an isolated Options Lab workspace to the existing WebView dashboard.
- Adds a transparent Black–Scholes calculator for theoretical premium and Delta, Gamma, Theta, Vega and Rho.
- Adds expiry/underlying sensitivity scenarios and a premium-at-risk estimate when a lot size is explicitly supplied.
- Labels all inputs as user-entered assumptions.
- Keeps the trade approval gate blocked because no authorized option-chain feed, verified timestamp, order-book liquidity, historical option-contract dataset, out-of-sample evidence or paper-trading record is connected.
- Does not place orders or emit BUY/SELL recommendations.
- Leaves existing saved Screener queries, fundamentals, chart workspace and existing navigation implementation intact apart from adding the new Options Lab tab.

## Not included / still required
1. Authorized broker/vendor options-chain adapter and contract-master synchronization.
2. Timestamped bid/ask, OI, volume, IV and market-depth validation.
3. Independent Greeks parity tests against a trusted provider/reference implementation.
4. Historical option-contract data with point-in-time expiry/strike/lot-size and corporate-action treatment.
5. Walk-forward and out-of-sample backtests with all-in costs and realistic fill/slippage modelling.
6. Paper-trading ledger and minimum evidence thresholds.
7. Risk engine and user-confirmed order workflow (if separately authorized later).

## Safety boundary
This is a calculator foundation, not a validated trading system. A successful Android build or UI test must not be described as evidence of strategy profitability or live option-data availability.

#!/usr/bin/env python3
"""Point-in-time factor-score backtest for PRO STOCK INTELLIGENCE.

Input CSV columns: asof_date,symbol,factor_score,next_period_return; OOS mode also requires return_start_date,return_end_date
- asof_date is the date the score was actually knowable (not restated later).
- next_period_return is decimal return over the next holding period (e.g. 0.04 = +4%).
- Include all eligible securities, including delisted names, to reduce survivorship bias.
This tool deliberately does not manufacture historical factor scores from today's fundamentals.
"""
import argparse, csv, math, statistics, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REQUIRED = {"asof_date", "symbol", "factor_score", "next_period_return"}
BOUNDARY_COLUMNS = {"return_start_date", "return_end_date"}

def parse_date(s):
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try: return datetime.strptime(s.strip(), fmt).date()
        except ValueError: pass
    raise ValueError(f"Invalid asof_date: {s!r}; use YYYY-MM-DD")

def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED - columns
        if missing: raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
        if bool(columns & BOUNDARY_COLUMNS) and not BOUNDARY_COLUMNS <= columns:
            raise ValueError("return_start_date and return_end_date must be supplied together")
        has_boundaries = BOUNDARY_COLUMNS <= columns
        groups = defaultdict(list); seen = set()
        for line, row in enumerate(reader, 2):
            try:
                date = parse_date(row["asof_date"])
                symbol = row["symbol"].strip().upper()
                score = float(row["factor_score"]); ret = float(row["next_period_return"])
                if not symbol or not math.isfinite(score) or not math.isfinite(ret): raise ValueError("blank symbol or non-finite number")
                if not 0 <= score <= 10: raise ValueError("factor_score must be between 0 and 10")
                if ret <= -1: raise ValueError("next_period_return must be greater than -1")
                record = (symbol, score, ret)
                if has_boundaries:
                    start = parse_date(row["return_start_date"])
                    end = parse_date(row["return_end_date"])
                    if start <= date: raise ValueError("return_start_date must be after asof_date to prevent same-period/look-ahead leakage")
                    if end < start: raise ValueError("return_end_date must be on or after return_start_date")
                    record = record + (start, end)
                key = (date, symbol)
                if key in seen: raise ValueError(f"duplicate symbol/date {symbol} {date}")
                seen.add(key); groups[date].append(record)
            except Exception as e: raise ValueError(f"Line {line}: {e}") from e
    if len(groups) < 2: raise ValueError("Need at least two as-of dates to evaluate a time series")
    return dict(sorted(groups.items()))

def max_drawdown(returns):
    wealth = peak = 1.0; worst = 0.0
    for r in returns:
        wealth *= 1 + r; peak = max(peak, wealth)
        worst = min(worst, wealth / peak - 1)
    return worst

def evaluate(groups, top_fraction=0.2, cost_bps=25.0, periods_per_year=12.0, oos_start=None):
    if not 0 < top_fraction <= 1: raise ValueError("top_fraction must be in (0,1]")
    if not math.isfinite(cost_bps) or not 0 <= cost_bps < 10000: raise ValueError("cost_bps must be finite and in [0, 10000) basis points")
    if not math.isfinite(periods_per_year) or periods_per_year <= 0: raise ValueError("periods_per_year must be positive")
    # If a holdout date is supplied, calculate reported metrics only on the holdout.
    # This ranking rule has no fitted parameters; pre-holdout rows are not used to
    # tune thresholds. The caller must still prove score timestamps and universe quality.
    oos_date = parse_date(str(oos_start)) if oos_start is not None and not hasattr(oos_start, "year") else oos_start
    evaluation_groups = {d: rows for d, rows in groups.items() if oos_date is None or d >= oos_date}
    if oos_date is not None:
        # Do not call a cutoff a genuine holdout unless each scored row includes
        # verifiable forward-return boundaries strictly after its score timestamp.
        for d, rows in evaluation_groups.items():
            for row in rows:
                if len(row) < 5:
                    raise ValueError("--oos-start requires return_start_date and return_end_date columns to verify forward-return boundaries")
                if row[3] <= d or row[4] < row[3]:
                    raise ValueError(f"Invalid forward-return boundary for {row[0]} on {d}")
    if len(evaluation_groups) < 2:
        raise ValueError("Evaluation window must contain at least two dates; choose an earlier --oos-start")
    portfolio, universe, turnover = [], [], []
    prior = set(); picked_count = 0
    for date, rows in sorted(evaluation_groups.items()):
        eligible = sorted(rows, key=lambda x: (x[1], x[0]), reverse=True)
        k = max(1, math.ceil(len(eligible) * top_fraction))
        chosen = eligible[:k]; selected = {x[0] for x in chosen}
        gross = statistics.mean(x[2] for x in chosen)
        bench = statistics.mean(x[2] for x in eligible)
        # Equal-weight portfolio replacement fraction (one-way turnover).
        # Jaccard distance understates turnover for equal-sized portfolios.
        turn = 1.0 if not prior else 1 - len(prior & selected) / max(1, len(prior), len(selected))
        # Charge costs on one-way turnover; first formation incurs cost on full invested value.
        net = gross - (cost_bps / 10000.0) * turn
        portfolio.append(net); universe.append(bench); turnover.append(turn)
        prior = selected; picked_count += len(chosen)
    def cagr(rs):
        wealth = math.prod(1 + x for x in rs)
        return wealth ** (periods_per_year / len(rs)) - 1 if wealth > 0 else -1.0
    def vol(rs): return statistics.stdev(rs) * math.sqrt(periods_per_year) if len(rs) > 1 else 0.0
    def sharpe(rs):
        v = vol(rs); return (statistics.mean(rs) * periods_per_year) / v if v else None
    return {
        "periods": len(portfolio), "dates": [str(x) for x in evaluation_groups], "periods_per_year": periods_per_year, "average_holdings": picked_count / len(portfolio),
        "evaluation_mode": "OUT_OF_SAMPLE_HOLDOUT_BOUNDARIES_VERIFIED" if oos_date is not None else "FULL_SAMPLE_EXPLORATORY",
        "oos_start": str(oos_date) if oos_date is not None else None,
        "minimum_periods_for_robust_review": 24,
        "sample_warning": "Fewer than 24 evaluated periods; performance statistics are highly uncertain." if len(portfolio) < 24 else None,
        "top_fraction": top_fraction, "transaction_cost_bps_per_turnover": cost_bps,
        "portfolio_cagr_annualized": cagr(portfolio), "universe_cagr_annualized": cagr(universe),
        "portfolio_volatility_annualized": vol(portfolio), "portfolio_sharpe_zero_rf": sharpe(portfolio),
        "portfolio_max_drawdown": max_drawdown(portfolio), "portfolio_hit_rate": sum(x > 0 for x in portfolio) / len(portfolio),
        "average_turnover": statistics.mean(turnover), "portfolio_period_returns_net": portfolio,
        "universe_period_returns": universe,
        "warning": "Exploratory only. Results depend on point-in-time scores, delisted-stock inclusion, correct forward returns, benchmark choice, and costs; not investment advice."
    }

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", help="Point-in-time score/forward-return CSV")
    ap.add_argument("--top-fraction", type=float, default=.2, help="Fraction of universe selected per date (default 0.2)")
    ap.add_argument("--cost-bps", type=float, default=25.0, help="All-in estimated transaction cost in basis points per one-way turnover (default 25; calibrate to broker, taxes and slippage)")
    ap.add_argument("--periods-per-year", type=float, default=12.0, help="Annualization frequency matching the CSV holding period (monthly=12, quarterly=4, weekly=52; default 12)")
    ap.add_argument("--oos-start", help="Holdout start date (YYYY-MM-DD); requires return_start_date and return_end_date columns proving forward returns occur after each score date")
    ap.add_argument("--out", help="Optional report path (Markdown)")
    args = ap.parse_args()
    try: result = evaluate(read_rows(args.csv), args.top_fraction, args.cost_bps, args.periods_per_year, args.oos_start)
    except Exception as e: print(f"ERROR: {e}", file=sys.stderr); return 2
    lines = ["# Factor Score Backtest", "", "- Boundary validation: verified per row" if args.oos_start else "- Boundary validation: not applicable (exploratory full sample)", f"- Evaluation mode: {result['evaluation_mode']}", f"- OOS start: {result['oos_start'] or 'not specified'}", f"- Periods: {result['periods']}", f"- Annualization frequency: {result['periods_per_year']:g} periods/year", f"- Annualized portfolio CAGR (net): {result['portfolio_cagr_annualized']:.2%}", f"- Annualized universe CAGR: {result['universe_cagr_annualized']:.2%}", f"- Annualized volatility: {result['portfolio_volatility_annualized']:.2%}", f"- Sharpe (0% risk-free): {result['portfolio_sharpe_zero_rf'] if result['portfolio_sharpe_zero_rf'] is not None else 'N/A'}", f"- Max drawdown: {result['portfolio_max_drawdown']:.2%}", f"- Hit rate: {result['portfolio_hit_rate']:.2%}", f"- Average turnover: {result['average_turnover']:.2%}", f"- All-in cost assumption: {result['transaction_cost_bps_per_turnover']} bps per one-way turnover", "", *( ["> " + result["sample_warning"]] if result["sample_warning"] else [] ), "> " + result["warning"], ""]
    report = "\n".join(lines)
    print(report)
    if args.out: Path(args.out).write_text(report, encoding="utf-8")
    return 0
if __name__ == "__main__": raise SystemExit(main())

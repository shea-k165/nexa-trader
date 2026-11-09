"""Offline research and paper simulation only. No broker connections."""
import argparse
import csv
import json
import math
from datetime import date
from pathlib import Path

def load_prices(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or not {'date', 'symbol', 'close'} <= rows[0].keys():
        raise ValueError('CSV requires date,symbol,close columns and data')
    series = {}
    seen = set()
    for row in rows:
        day = date.fromisoformat(row['date']).isoformat()
        symbol = row['symbol'].strip().upper()
        price = float(row['close'])
        if not symbol or not math.isfinite(price) or price <= 0:
            raise ValueError('Symbol and positive finite close required')
        if (symbol, day) in seen:
            raise ValueError('Duplicate symbol/date')
        seen.add((symbol, day))
        series.setdefault(symbol, []).append((day, price))
    for values in series.values():
        values.sort()
        if len(values) < 6:
            raise ValueError('Each symbol needs at least six price observations')
    return series

def simulate(values, initial=10000.0, fee_bps=10.0):
    if not math.isfinite(initial) or initial <= 0 or not math.isfinite(fee_bps) or not 0 <= fee_bps <= 1000:
        raise ValueError('Invalid initial cash or fee')
    cash, shares, peak, drawdown = initial, 0, initial, 0.0
    trades = []
    # Signal uses yesterday and earlier; execution uses today's close.
    # This is a simplified close-fill simulation, not a realistic execution model.
    for i, (day, price) in enumerate(values):
        if i >= 5:
            signal = values[i-1][1] > sum(p for _, p in values[i-5:i]) / 5
            if signal and shares == 0:
                qty = int((cash * 0.20) / (price * (1 + fee_bps/10000)))
                if qty:
                    cash -= qty * price * (1 + fee_bps/10000)
                    shares = qty
                    trades.append({'date': day, 'side': 'PAPER BUY', 'shares': qty, 'price': price})
            elif not signal and shares:
                cash += shares * price * (1 - fee_bps/10000)
                trades.append({'date': day, 'side': 'PAPER SELL', 'shares': shares, 'price': price})
                shares = 0
        equity = cash + shares * price
        peak = max(peak, equity)
        drawdown = max(drawdown, 1-equity/peak)
    return {'initial_cash': initial, 'cash': round(cash, 2), 'shares': shares,
            'equity': round(equity, 2), 'return_pct': round((equity/initial-1)*100, 4),
            'max_drawdown_pct': round(drawdown*100, 4), 'trades': trades}

def research(series, initial=10000, fee_bps=10):
    result = {}
    for symbol, values in sorted(series.items()):
        prices = [p for _, p in values]
        result[symbol] = {'first_date': values[0][0], 'last_date': values[-1][0],
            'observations': len(values), 'last_close': prices[-1],
            'period_change_pct': round((prices[-1]/prices[0]-1)*100, 4),
            'paper_account': simulate(values, initial, fee_bps)}
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['demo', 'csv'], default='demo')
    parser.add_argument('--prices', type=Path)
    parser.add_argument('--cash', type=float, default=10000)
    parser.add_argument('--fee-bps', type=float, default=10)
    parser.add_argument('--output', type=Path, default=Path('output'))
    args = parser.parse_args()
    if args.mode == 'csv' and args.prices is None:
        parser.error('--prices is required for csv mode')
    try:
        source = args.prices if args.mode == 'csv' else Path(__file__).parent/'data/demo.csv'
        report = {'mode': 'PAPER ONLY', 'source': str(source),
            'synthetic_demo': args.mode == 'demo',
            'limitations': 'Separate account per symbol; no portfolio aggregation. No real orders. No forecasts. Unadjusted CSV prices may distort returns. No spread, tax, dividends or liquidity model. Open positions marked to last close.',
            'symbols': research(load_prices(source), args.cash, args.fee_bps)}
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output/'research.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        lines = ['# Nexa Trader: PAPER ONLY', '', str(report['limitations']), '',
                 'SYNTHETIC DEMO DATA' if report['synthetic_demo'] else 'User supplied historical CSV', '']
        for symbol, r in report['symbols'].items():
            lines.append(f"{symbol}: {r['observations']} observations; paper equity {r['paper_account']['equity']}; period change {r['period_change_pct']}%")
        (args.output/'research.md').write_text('\n'.join(lines), encoding='utf-8')
        print('Paper research saved to', args.output.resolve())
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f'Input error: {exc}\n')

if __name__ == '__main__':
    main()

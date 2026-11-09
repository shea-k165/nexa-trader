import tempfile
import unittest
from pathlib import Path
from trader import load_prices, simulate, research

class TraderTests(unittest.TestCase):
    def test_demo(self):
        r = research(load_prices('data/demo.csv'))['DEMO']
        self.assertEqual(r['observations'], 20)
        self.assertGreater(len(r['paper_account']['trades']), 0)
    def test_no_lookahead(self):
        v = [(str(i), float(100+i)) for i in range(8)]
        a = simulate(v)
        v[5] = ('5', 200.0)
        b = simulate(v)
        self.assertEqual(a['trades'][0]['date'], '5')
        self.assertEqual(b['trades'][0]['date'], '5')
        self.assertEqual(b['trades'][0]['price'], 200)
    def test_flat_no_trades(self):
        r = simulate([(str(i), 100.0) for i in range(10)])
        self.assertEqual(r['equity'], 10000)
        self.assertEqual(r['trades'], [])
    def test_fee_and_allocation(self):
        r = simulate([(str(i), float(i+100)) for i in range(6)])
        self.assertLessEqual(r['trades'][0]['shares']*105*1.001, 2000)
        self.assertLess(r['equity'], 10000)
    def test_invalid_cash(self):
        for cash in [0, -1, float('nan')]:
            with self.assertRaises(ValueError): simulate([('1',100)], cash)
    def test_exit_accounting(self):
        values = [(str(i), float(p)) for i,p in enumerate([100,101,102,103,104,105,90,80])]
        r = simulate(values)
        self.assertEqual([t['side'] for t in r['trades']], ['PAPER BUY','PAPER SELL'])
        self.assertEqual(r['shares'], 0)
        self.assertAlmostEqual(r['cash'], 9521.49)
        self.assertEqual(r['equity'], r['cash'])
        self.assertGreater(r['max_drawdown_pct'], 0)
    def test_bad_csv(self):
        for text in ['date,symbol,close\n2026-01-01,A,nan', 'date,symbol,close\n2026-01-01,A,1\n2026-01-01,A,2', 'x,y\n1,2']:
            with tempfile.TemporaryDirectory() as t:
                p=Path(t)/'bad.csv'; p.write_text(text)
                with self.assertRaises(ValueError): load_prices(p)

if __name__ == '__main__': unittest.main()

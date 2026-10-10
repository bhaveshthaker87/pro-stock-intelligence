import importlib.util, tempfile, unittest
from pathlib import Path
p=Path(__file__).parents[1]/'tools'/'factor_score_backtest.py'
spec=importlib.util.spec_from_file_location('backtest',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class BacktestTests(unittest.TestCase):
    def test_portfolio_metrics_and_costs(self):
        groups={
          m.parse_date('2025-01-31'):[('AAA',9,.10),('BBB',4,-.05),('CCC',2,.02)],
          m.parse_date('2025-02-28'):[('AAA',9,.05),('BBB',4,.01),('CCC',2,-.02)],
          m.parse_date('2025-03-31'):[('AAA',9,-.03),('BBB',4,.02),('CCC',2,.01)],
        }
        r=m.evaluate(groups,1/3,10)
        self.assertEqual(r['periods'],3); self.assertEqual(len(r['portfolio_period_returns_net']),3)
        self.assertAlmostEqual(r['portfolio_period_returns_net'][0],.099)
        self.assertTrue(0 <= r['average_turnover'] <= 1)
        self.assertTrue(-1 <= r['portfolio_max_drawdown'] <= 0)
    def test_factor_score_range_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'x.csv'; f.write_text('asof_date,symbol,factor_score,next_period_return\n2025-01-31,AAA,11,.1\n2025-02-28,AAA,9,.1\n',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'between 0 and 10'): m.read_rows(f)
    def test_annualization_frequency_is_configurable(self):
        groups={m.parse_date('2025-01-31'):[('AAA',10,.10)],m.parse_date('2025-04-30'):[('AAA',10,.10)]}
        monthly=m.evaluate(groups,1,0,12)
        quarterly=m.evaluate(groups,1,0,4)
        self.assertGreater(monthly['portfolio_cagr_annualized'],quarterly['portfolio_cagr_annualized'])
        self.assertEqual(quarterly['periods_per_year'],4)
    def test_turnover_is_one_way_replacement_fraction(self):
        groups={m.parse_date('2025-01-31'):[('AAA',10,.1),('BBB',1,.0)],m.parse_date('2025-02-28'):[('AAA',1,.0),('BBB',10,.1)]}
        r=m.evaluate(groups,.5,0)
        self.assertEqual(r['average_turnover'],1.0)
    def test_duplicate_symbols_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'x.csv'; f.write_text('asof_date,symbol,factor_score,next_period_return\n2025-01-31,AAA,9,.1\n2025-01-31,AAA,8,.2\n2025-02-28,AAA,9,.1\n',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'duplicate'): m.read_rows(f)
    def test_point_in_time_minimum_periods(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'x.csv'; f.write_text('asof_date,symbol,factor_score,next_period_return\n2025-01-31,AAA,9,.1\n',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'two as-of dates'): m.read_rows(f)
if __name__=='__main__': unittest.main()

import copy
import unittest
from model import load, calculate, validate, variance


class ForecastTests(unittest.TestCase):
    def setUp(self): self.rows=load()
    def test_q1_actuals_frozen(self):
        changed=copy.deepcopy(self.rows); changed[2]['forecast_delivery_q']=4
        self.assertEqual(calculate(self.rows,'forecast')[0][0],calculate(changed,'forecast')[0][0])
    def test_closed_delivery_rejected(self):
        self.rows[0]['forecast_fee']=46
        with self.assertRaises(ValueError): validate(self.rows)
    def test_cash_reconciles_each_quarter(self):
        for r in calculate(self.rows,'forecast')[0]: self.assertAlmostEqual(r['cash_bridge_error'],0)
    def test_horizon_collects_everything(self):
        q,_=calculate(self.rows,'forecast')
        self.assertAlmostEqual(q[-1]['content_asset'],0)
        self.assertAlmostEqual(q[-1]['receivables'],0)
        self.assertAlmostEqual(q[-1]['participation_payable'],0)
        self.assertAlmostEqual(q[-1]['cumulative_cash'],sum(r['contribution'] for r in q))
    def test_variance_fully_explained(self):
        b,_=calculate(self.rows,'budget'); f,_=calculate(self.rows,'forecast')
        for x,y,z in zip(b,f,variance(self.rows)):
            self.assertAlmostEqual(y['contribution']-x['contribution'],z['timing']+z['fee']+z['cost'])
    def test_pure_delay_preserves_total_value(self):
        a=calculate(self.rows,'forecast')[0]
        self.rows[1]['forecast_delivery_q']=3
        b=calculate(self.rows,'forecast')[0]
        self.assertAlmostEqual(sum(r['contribution'] for r in a),sum(r['contribution'] for r in b))
        self.assertNotEqual(a[1]['revenue'],b[1]['revenue'])
    def test_invalid_data(self):
        for key,value in [('forecast_delivery_q',6),('forecast_cost',1),('participation_rate',1.1)]:
            rows=copy.deepcopy(self.rows); rows[1][key]=value
            with self.assertRaises(ValueError): validate(rows)
        with self.assertRaises(ValueError): validate(self.rows+self.rows[:1])


if __name__=='__main__': unittest.main()

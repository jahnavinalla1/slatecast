"""Fictional scripted-TV slate: quarterly delivery, contribution and cash bridge.

Python 3.10+, standard library only. All financial values USD millions.
Project contribution uses a simplified cost-at-delivery convention, NOT Sony OI.
"""
import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PERIODS = ['FY26 Q1 actual', 'FY26 Q2', 'FY26 Q3', 'FY26 Q4', 'FY27 Q1', 'FY27 Q2']


def load():
    with (ROOT / 'data/series.csv').open() as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in r:
            if k not in ('id', 'title'):
                r[k] = int(r[k]) if k.endswith('_q') else float(r[k])
    validate(rows)
    return rows


def validate(rows):
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Series IDs must be nonempty and unique')
    for r in rows:
        for case in ('budget', 'forecast'):
            q = r[f'{case}_delivery_q']
            if q != int(q) or not 1 <= q <= 5:
                raise ValueError('Delivery quarter must be an integer from 1 to 5')
            if r[f'{case}_cost'] < r['q1_cash_spend'] or r['q1_cash_spend'] < 0:
                raise ValueError('EAC cannot be below cash already spent')
            if r[f'{case}_fee'] < 0 or not 0 <= r['participation_rate'] <= 1:
                raise ValueError('Invalid fee or participation rate')
        if r['budget_delivery_q'] == 1 or r['forecast_delivery_q'] == 1:
            if any(r[f'budget_{k}'] != r[f'forecast_{k}'] for k in ('delivery_q', 'fee', 'cost')):
                raise ValueError('Closed Q1 delivery economics cannot change')
            if r['q1_cash_spend'] != r['budget_cost']:
                raise ValueError('Q1 delivered title must be fully paid under this model')


def calculate(rows, case):
    validate(rows)
    if case not in ('budget', 'forecast'):
        raise ValueError('Unknown case')
    detail = []
    for r in rows:
        dq, fee, cost = (r[f'{case}_{k}'] for k in ('delivery_q', 'fee', 'cost'))
        for q in range(1, 7):
            revenue = fee if q == dq else 0.0
            delivered_cost = cost if q == dq else 0.0
            spend = r['q1_cash_spend'] if q == 1 else (cost-r['q1_cash_spend'])/(dq-1) if 1 < q <= dq else 0.0
            receipts = fee if q == dq+1 else 0.0
            participation = revenue*r['participation_rate']
            paid_participation = receipts*r['participation_rate']
            detail.append(dict(id=r['id'], quarter=q, revenue=revenue, delivered_cost=delivered_cost,
                               participation=participation, production_cash=spend, receipts=receipts,
                               participation_cash=paid_participation))
    # SQL aggregation is deliberately part of the executable reporting pipeline.
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE detail (id TEXT, quarter INTEGER, revenue REAL, delivered_cost REAL, participation REAL, production_cash REAL, receipts REAL, participation_cash REAL)')
    db.executemany('INSERT INTO detail VALUES (?,?,?,?,?,?,?,?)', [tuple(r.values()) for r in detail])
    query = (ROOT/'analysis.sql').read_text()
    cur = db.execute(query)
    quarterly = [dict(zip([d[0] for d in cur.description], row)) for row in cur.fetchall()]
    asset = ar = payable = cumulative_cash = 0.0
    for r in quarterly:
        previous = (asset, ar, payable)
        asset += r['production_cash']-r['delivered_cost']
        ar += r['revenue']-r['receipts']
        payable += r['participation']-r['participation_cash']
        cumulative_cash += r['net_cash']
        cash_bridge = r['contribution']-(asset-previous[0])-(ar-previous[1])+(payable-previous[2])
        r.update(period=PERIODS[r['quarter']-1], content_asset=asset, receivables=ar,
                 participation_payable=payable, cumulative_cash=cumulative_cash,
                 cash_bridge_error=cash_bridge-r['net_cash'])
    return quarterly, detail


def variance(rows):
    """Sequential bridge: delivery timing first, then fee, then EAC changes."""
    out=[]
    for q in range(1, 7):
        timing=fee=cost=0.0
        for r in rows:
            b, f = int(r['budget_delivery_q']==q), int(r['forecast_delivery_q']==q)
            timing += (f-b)*(r['budget_fee']*(1-r['participation_rate'])-r['budget_cost'])
            fee += f*(r['forecast_fee']-r['budget_fee'])*(1-r['participation_rate'])
            cost -= f*(r['forecast_cost']-r['budget_cost'])
        out.append(dict(quarter=q, timing=timing, fee=fee, cost=cost))
    return out


def main():
    rows=load()
    budget,_=calculate(rows,'budget')
    forecast,detail=calculate(rows,'forecast')
    bridge=variance(rows)
    results=ROOT/'results'; results.mkdir(exist_ok=True)
    for name, records in [('budget',budget),('forecast',forecast),('title_quarters',detail),('variance',bridge)]:
        with (results/f'{name}.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=records[0].keys()); w.writeheader(); w.writerows(records)
    metrics={
        'fy26_budget_revenue':sum(x['revenue'] for x in budget[:4]),
        'fy26_forecast_revenue':sum(x['revenue'] for x in forecast[:4]),
        'fy26_budget_contribution':sum(x['contribution'] for x in budget[:4]),
        'fy26_forecast_contribution':sum(x['contribution'] for x in forecast[:4]),
        'fy26_forecast_net_cash':sum(x['net_cash'] for x in forecast[:4]),
        'peak_cumulative_funding':max(0,-min(x['cumulative_cash'] for x in forecast)),
        'spillover_revenue':sum(x['revenue'] for x in forecast[4:]),
        'fy26_bridge':{k:sum(x[k] for x in bridge[:4]) for k in ('timing','fee','cost')},
        'full_horizon_forecast_contribution':sum(x['contribution'] for x in forecast),
        'max_cash_bridge_error':max(abs(x['cash_bridge_error']) for x in forecast)}
    (results/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    print(json.dumps(metrics,indent=2))


if __name__=='__main__':
    main()

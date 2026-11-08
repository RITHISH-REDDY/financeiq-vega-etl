from contextlib import closing
"""Transparent SQL-backed cash-basis management reports (not formal GAAP statements)."""
from .pipeline import connect, DB

def summary(company='All', month='All', db=DB):
    where, params = [], []
    if company != 'All': where.append('company=?'); params.append(company)
    if month != 'All': where.append('substr(date,1,7)=?'); params.append(month)
    clause = ' WHERE ' + ' AND '.join(where) if where else ''
    with closing(connect(db)) as con, con:
        rows = [dict(r) for r in con.execute('SELECT * FROM transactions'+clause+' ORDER BY date DESC,transaction_id DESC',params)]
    # Reviewed entries remain marked as non-reconciled until a matching book entry exists.
    # All bank entries included for cash-basis illustrative reporting, even pending review.
    revenue = round(sum(r['amount'] for r in rows if r['direction']=='credit'),2)
    expenses = round(sum(r['amount'] for r in rows if r['direction']=='debit'),2)
    categories = {}
    monthly = {}
    for r in rows:
        m = r['date'][:7]
        monthly.setdefault(m, {'month':m,'revenue':0,'expenses':0})
        monthly[m]['revenue' if r['direction']=='credit' else 'expenses'] += r['amount']
        if r['direction']=='debit': categories[r['category']] = round(categories.get(r['category'],0)+r['amount'],2)
    trend = []
    for m in sorted(monthly):
        item = monthly[m]
        trend.append({k:round(v,2) if isinstance(v,(float,int)) else v for k,v in item.items()})
    return {'revenue':revenue,'expenses':expenses,'net_cash_surplus':round(revenue-expenses,2),
            'margin_pct':round((revenue-expenses)/revenue*100,1) if revenue else 0,
            'transactions':rows,'categories':categories,'monthly':trend,
            'review_count':sum(r['review_status']=='Needs Review' for r in rows),
            'unmatched_count':sum(not r['matched_ledger'] for r in rows)}


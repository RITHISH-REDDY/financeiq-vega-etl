from contextlib import closing
"""CSV ingestion, company mapping, categorization, reconciliation and SQLite loading."""
import csv
import sqlite3
import math
from datetime import date
from pathlib import Path
from .generate_data import ROOT

DB = ROOT / 'data' / 'finance.db'
ACCOUNTS = {'VEGA-RENTALS-001': 'Vega Self Drive Car'}
RULES = [
    ('payroll', 'Payroll'), ('aws', 'Cloud Infrastructure'), ('workspace', 'Software'),
    ('rent', 'Rent'), ('ads', 'Marketing'), ('contractor', 'Contractors'),
    ('maintenance', 'Vehicle Maintenance'), ('insurance', 'Insurance'), ('fuel', 'Fuel')
]

def classify(merchant, direction):
    if direction == 'credit': return 'Revenue'
    m = merchant.lower()
    return next((category for key, category in RULES if key in m), 'Needs Review')

def connect(db=DB):
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    return con

def build(db=DB, data_dir=None):
    data_dir = Path(data_dir) if data_dir is not None else ROOT / 'data'
    with closing(connect(db)) as con, con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS transactions (
          transaction_id TEXT PRIMARY KEY, date TEXT NOT NULL, company TEXT NOT NULL,
          account_id TEXT NOT NULL, merchant TEXT NOT NULL, amount REAL NOT NULL,
          direction TEXT NOT NULL CHECK(direction IN ('credit','debit')),
          category TEXT NOT NULL, matched_ledger INTEGER NOT NULL DEFAULT 0,
          review_status TEXT NOT NULL DEFAULT 'Approved'
        );
        CREATE INDEX IF NOT EXISTS idx_company_date ON transactions(company,date);
        ''')
        with (data_dir / 'quickbooks_style_ledger.csv').open(newline='',encoding='utf-8') as f:
            ledger = {(r['date'],r['company'],r['description'],round(float(r['amount']),2),r['category']) for r in csv.DictReader(f)}
        seen = {}
        with (data_dir / 'plaid_style_transactions.csv').open(newline='',encoding='utf-8') as f:
            for r in csv.DictReader(f):
                r = {key: value.strip() for key, value in r.items()}
                date.fromisoformat(r['date'])
                if not r['transaction_id'] or not r['merchant']:
                    raise ValueError('Transaction ID and merchant are required')
                if r['direction'] not in ('credit', 'debit'):
                    raise ValueError('Invalid direction')
                if r['transaction_id'] in seen and seen[r['transaction_id']] != r:
                    raise ValueError('Conflicting duplicate transaction ID')
                seen[r['transaction_id']] = r
                company = ACCOUNTS.get(r['account_id'])
                if company is None: raise ValueError(f"Unknown account: {r['account_id']}")
                amount = round(float(r['amount']),2)
                if not math.isfinite(amount) or amount < 0: raise ValueError('Amounts must be finite and nonnegative; direction determines sign')
                category = classify(r['merchant'],r['direction'])
                matched = int((r['date'],company,r['merchant'],amount,category) in ledger)
                status = 'Approved' if matched and category!='Needs Review' else 'Needs Review'
                con.execute('''INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?)
                  ON CONFLICT(transaction_id) DO UPDATE SET
                  date=excluded.date, company=excluded.company, account_id=excluded.account_id,
                  merchant=excluded.merchant, amount=excluded.amount, direction=excluded.direction,
                  matched_ledger=excluded.matched_ledger,
                  category=CASE WHEN transactions.review_status='Reviewed' THEN transactions.category ELSE excluded.category END,
                  review_status=CASE WHEN transactions.review_status='Reviewed' THEN 'Reviewed' ELSE excluded.review_status END''',
                  (r['transaction_id'],r['date'],company,r['account_id'],r['merchant'],amount,r['direction'],category,matched,status))
        return con.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]

def approve(transaction_id, category, db=DB):
    if not category.strip() or category in ('Needs Review','Revenue'):
        raise ValueError('Choose a valid expense category')
    with closing(connect(db)) as con, con:
        cur = con.execute('''UPDATE transactions SET category=?,review_status='Reviewed'
            WHERE transaction_id=? AND direction='debit' AND review_status='Needs Review' ''', (category,transaction_id))
        return cur.rowcount

if __name__ == '__main__':
    print('Loaded transactions:', build())


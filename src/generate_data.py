"""Generate fully synthetic, reproducible bank and bookkeeping records."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
COMPANIES = {
    'Vega Self Drive Car': {
        'account': 'VEGA-RENTALS-001',
        'income': [('Daily self-drive bookings', 7500), ('Corporate self-drive rentals', 4300), ('Weekend rental bookings', 2800)],
        'expenses': [('Vehicle maintenance', 'Vehicle Maintenance', 1450), ('Commercial auto insurance', 'Insurance', 1250), ('Fuel station', 'Fuel', 680), ('Employee payroll', 'Payroll', 3100), ('Google Ads', 'Marketing', 430), ('Parking facility rent', 'Rent', 850)]
    }
}

def generate(seed=42, months=6, data_dir=DATA):
    data_dir = Path(data_dir)
    random.seed(seed)
    data_dir.mkdir(parents=True, exist_ok=True)
    bank, books = [], []
    txid = 0
    for company, cfg in COMPANIES.items():
        for month in range(1, months + 1):
            year = 2026
            for desc, base in cfg['income']:
                txid += 1
                amount = round(base * random.uniform(.78, 1.18), 2)
                dt = date(year, month, random.randint(3, 24)).isoformat()
                bank.append([f'BANK-{txid:05}', dt, cfg['account'], desc, amount, 'credit'])
                books.append([f'QB-{txid:05}', dt, company, desc, amount, 'Revenue'])
            for desc, category, base in cfg['expenses']:
                txid += 1
                amount = round(base * random.uniform(.8, 1.22), 2)
                dt = date(year, month, random.randint(3, 25)).isoformat()
                bank.append([f'BANK-{txid:05}', dt, cfg['account'], desc, amount, 'debit'])
                books.append([f'QB-{txid:05}', dt, company, desc, amount, category])
    # One exception to show the review workflow; deliberately absent from books.
    for company, account in [('Vega Self Drive Car', 'VEGA-RENTALS-001')]:
        txid += 1
        bank.append([f'BANK-{txid:05}', '2026-06-27', account, 'Unidentified vendor ACH', 275.00, 'debit'])
    # Duplicate import demonstrates idempotency.
    bank.append(bank[0].copy())
    def write(path, headers, rows):
        with path.open('w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(headers); w.writerows(rows)
    write(data_dir / 'plaid_style_transactions.csv', ['transaction_id','date','account_id','merchant','amount','direction'], bank)
    write(data_dir / 'quickbooks_style_ledger.csv', ['entry_id','date','company','description','amount','category'], books)
    return len(bank), len(books)

if __name__ == '__main__':
    print('Generated bank rows, book rows:', generate())

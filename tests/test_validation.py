import csv
import sqlite3
import pytest
from src.generate_data import generate
from src.pipeline import build, connect
from src.reports import summary


def read_bank(path):
    with (path / 'plaid_style_transactions.csv').open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def write_bank(path, rows):
    with (path / 'plaid_style_transactions.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_generation_is_reproducible(tmp_path):
    assert generate(data_dir=tmp_path) == (56, 54)
    before = (tmp_path / 'plaid_style_transactions.csv').read_bytes()
    generate(data_dir=tmp_path)
    assert (tmp_path / 'plaid_style_transactions.csv').read_bytes() == before


@pytest.mark.parametrize('field,value', [
    ('account_id', 'OTHER-COMPANY'), ('amount', '-10'), ('amount', 'nan'),
    ('amount', 'inf'), ('date', '2026-02-30'), ('direction', 'transfer'),
    ('transaction_id', ''), ('merchant', '')])
def test_invalid_import_rolls_back(tmp_path, field, value):
    generate(data_dir=tmp_path)
    db = tmp_path / 'test.db'
    build(db, tmp_path)
    before = summary(db=db)
    rows = read_bank(tmp_path)
    rows[0]['amount'] = '1.00'  # An earlier valid update must also roll back.
    rows.pop()  # Remove the intentional duplicate.
    rows[-1][field] = value
    write_bank(tmp_path, rows)
    with pytest.raises((ValueError, sqlite3.IntegrityError)):
        build(db, tmp_path)
    assert summary(db=db) == before


def test_conflicting_duplicate_rejected(tmp_path):
    generate(data_dir=tmp_path)
    rows = read_bank(tmp_path)
    rows[-1]['amount'] = '1.00'
    write_bank(tmp_path, rows)
    with pytest.raises(ValueError, match='Conflicting duplicate'):
        build(tmp_path / 'test.db', tmp_path)


def test_cash_totals_and_month_filter(tmp_path):
    generate(data_dir=tmp_path)
    db = tmp_path / 'test.db'
    build(db, tmp_path)
    data = summary(db=db)
    rows = read_bank(tmp_path)
    unique = {r['transaction_id']: r for r in rows}.values()
    receipts = round(sum(float(r['amount']) for r in unique if r['direction'] == 'credit'), 2)
    payments = round(sum(float(r['amount']) for r in unique if r['direction'] == 'debit'), 2)
    assert data['revenue'] == receipts
    assert data['expenses'] == payments
    assert data['net_cash_surplus'] == round(receipts - payments, 2)
    assert data['unmatched_count'] == 1
    january = summary(month='2026-01', db=db)
    assert len(january['transactions']) == 9
    assert all(r['date'].startswith('2026-01') for r in january['transactions'])

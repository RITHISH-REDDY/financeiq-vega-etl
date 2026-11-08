from src.generate_data import generate
from src.pipeline import build, connect, classify, approve
from src.reports import summary

def test_classification():
    assert classify('AWS cloud hosting','debit')=='Cloud Infrastructure'
    assert classify('Rental bookings','credit')=='Revenue'
    assert classify('Unidentified vendor ACH','debit')=='Needs Review'

def test_pipeline_idempotency_and_single_company(tmp_path):
    generate(data_dir=tmp_path)
    db=tmp_path/'test.db'
    n=build(db, tmp_path)
    assert n==55  # 1 company * 6 months * 9 transactions + 1 exception
    assert build(db, tmp_path)==n
    with connect(db) as con:
        assert con.execute('SELECT COUNT(DISTINCT company) FROM transactions').fetchone()[0]==1
        assert con.execute('SELECT DISTINCT company FROM transactions').fetchone()[0]=='Vega Self Drive Car'
    data=summary('Vega Self Drive Car',db=db)
    assert data['revenue']>0 and data['expenses']>0
    assert data['review_count']==1
    assert approve('BANK-00055','Vehicle Maintenance',db)==1
    assert summary('Vega Self Drive Car',db=db)['review_count']==0
    assert build(db, tmp_path)==n
    assert summary('Vega Self Drive Car',db=db)['review_count']==0

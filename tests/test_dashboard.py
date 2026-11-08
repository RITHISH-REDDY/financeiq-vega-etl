from pathlib import Path
from streamlit.testing.v1 import AppTest
from src.generate_data import generate
from src.pipeline import build
from src import pipeline, reports, assistant


def test_dashboard_filters_and_local_summary(tmp_path, monkeypatch):
    generate(data_dir=tmp_path)
    db = tmp_path / 'dashboard.db'
    build(db, tmp_path)
    original_summary = reports.summary
    def isolated_summary(company='All', month='All'):
        return original_summary(company, month, db=db)
    monkeypatch.setattr(pipeline, 'DB', db)
    monkeypatch.setattr(reports, 'summary', isolated_summary)
    monkeypatch.setattr(assistant, 'summary', isolated_summary)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=30)
    assert not app.exception
    assert len(app.metric) == 4
    next(item for item in app.selectbox if item.label == 'Month').select('2026-01').run()
    assert not app.exception
    assert app.metric[0].value != '$0'
    next(button for button in app.button if button.label == 'Analyze').click().run()
    assert not app.exception
    assert any('Demo mode: Revenue' in item.value for item in app.markdown)


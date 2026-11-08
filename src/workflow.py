"""Run the reproducible demo, verify it, and log failures for unattended ETL."""
import argparse
import logging
from logging.handlers import RotatingFileHandler
import subprocess
import sys
from .generate_data import ROOT, generate
from .pipeline import build
from .reports import summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', nargs='?', choices=['etl', 'verify'], default='verify')
    args = parser.parse_args()
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.StreamHandler(), RotatingFileHandler(
                            logs / 'workflow.log', maxBytes=1_000_000, backupCount=3, encoding='utf-8')])
    try:
        if args.mode != 'etl':
            subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=ROOT, check=True)
        # Generate only on interactive/verification runs. Scheduled ETL never regenerates CSVs.
        if args.mode != 'etl':
            logging.info('Generated synthetic rows: bank=%s books=%s', *generate())
        count = build()
        report = summary('Vega Self Drive Car')
        logging.info('Loaded %s unique transactions; receipts=%.2f payments=%.2f surplus=%.2f pending=%s',
                     count, report['revenue'], report['expenses'], report['net_cash_surplus'], report['review_count'])
        return 0
    except Exception:
        logging.exception('Workflow failed')
        return 1


if __name__ == '__main__':
    sys.exit(main())

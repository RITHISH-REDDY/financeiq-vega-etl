"""Optional LLM explanation of precomputed aggregates; no SQL or bank credentials exposed."""
import os
from .reports import summary

def answer(question, company='All', month='All'):
    data = summary(company, month)
    safe = {k:v for k,v in data.items() if k!='transactions'}
    if not os.getenv('OPENAI_API_KEY'):
        return (f"Demo mode: Revenue ${data['revenue']:,.2f}; expenses ${data['expenses']:,.2f}; "
                f"net cash surplus ${data['net_cash_surplus']:,.2f}; margin {data['margin_pct']}%. "
                f"{data['review_count']} transactions require review. Set OPENAI_API_KEY for AI explanations.")
    from openai import OpenAI
    client = OpenAI()
    result = client.responses.create(
        model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'),
        instructions=('You are a financial analytics explainer. Use ONLY the supplied aggregates. '
                      'Do not invent facts, offer definitive tax advice, or call cash surplus GAAP net income. '
                      'State that figures are synthetic cash-basis estimates and pending reviews may affect accuracy.'),
        input=f'Question: {question}\nCompany: {company}\nMonth: {month}\nAggregates: {safe}',
        max_output_tokens=350)
    return result.output_text

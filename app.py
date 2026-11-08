"""Run: streamlit run app.py"""
import pandas as pd
import plotly.express as px
import streamlit as st
from src.generate_data import generate
from src.pipeline import build, approve, DB
from src.reports import summary
from src.assistant import answer

st.set_page_config(page_title='FinanceIQ | Vega Self Drive Car',page_icon='📊',layout='wide')
st.title('📊 FinanceIQ')
st.caption('Vega Self Drive Car | Synthetic financial analytics demo — not a formal income statement')
if not DB.exists():
    generate(); build()
with st.sidebar:
    st.header('Filters')
    company = 'Vega Self Drive Car'
    month = st.selectbox('Month',['All']+[f'2026-{m:02}' for m in range(1,7)])
    if st.button('Reload synthetic CSV data'):
        build(); st.success('Import complete; existing reviewed categories preserved.')
    st.info('Bank and QuickBooks data are simulated. No live Plaid or QuickBooks connection.')
d = summary(company,month)
a,b,c,e = st.columns(4)
a.metric('Cash receipts',f"${d['revenue']:,.0f}")
b.metric('Cash payments',f"${d['expenses']:,.0f}")
c.metric('Net cash surplus',f"${d['net_cash_surplus']:,.0f}")
e.metric('Surplus margin',f"{d['margin_pct']}%")
t1,t2,t3=st.tabs(['Overview','Transactions & review','AI financial assistant'])
with t1:
    left,right=st.columns(2)
    with left:
        st.subheader('Monthly cash activity')
        if d['monthly']:
            df=pd.DataFrame(d['monthly']).melt('month',value_vars=['revenue','expenses'],var_name='Type',value_name='USD')
            st.plotly_chart(px.bar(df,x='month',y='USD',color='Type',barmode='group'),use_container_width=True)
    with right:
        st.subheader('Expense categories')
        if d['categories']:
            df=pd.DataFrame([{'Category':k,'USD':v} for k,v in d['categories'].items()])
            st.plotly_chart(px.pie(df,names='Category',values='USD',hole=.42),use_container_width=True)
    st.warning(f"{d['review_count']} transactions require review; {d['unmatched_count']} bank entries lack a matching synthetic bookkeeping record.") if d['review_count'] else st.success('No pending classification reviews.')
with t2:
    st.subheader('Imported bank transactions')
    st.dataframe(pd.DataFrame(d['transactions']),use_container_width=True,hide_index=True)
    pending=[r for r in d['transactions'] if r['review_status']=='Needs Review' and r['direction']=='debit']
    if pending:
        with st.form('review'):
            chosen=st.selectbox('Pending transaction',[r['transaction_id'] for r in pending])
            category=st.selectbox('Approve category',['Professional Services','Office Supplies','Vehicle Maintenance','Software','Other Expense'])
            if st.form_submit_button('Approve classification'):
                approve(chosen,category); st.rerun()
    else:
        st.success('No transactions awaiting classification.')
with t3:
    st.subheader('Ask about the financial data')
    question=st.text_input('Question',value='What is the revenue, expense and surplus summary?')
    if st.button('Analyze'):
        with st.spinner('Preparing response...'):
            try: st.write(answer(question,company,month))
            except Exception as ex: st.error(f'AI service unavailable: {type(ex).__name__}. Check API configuration.')
    st.caption('LLM receives summary aggregates, not raw transaction details. Set OPENAI_API_KEY to enable.')
st.divider()
st.caption('Method: cash inflows less cash outflows, not accrual P&L or tax liability. Excludes complex adjustments, loans, transfers and tax accounting.')

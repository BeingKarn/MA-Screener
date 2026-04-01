 
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from screener    import run_screening
from valuation   import value_top_targets
from memo_engine import generate_all_memos
 
st.set_page_config(
    page_title='M&A Screener',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded'
)
 
# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.title('⚙️ Settings')
    st.markdown('**Data Source:** Yahoo Finance (Free)')
    st.markdown('**No API key required**')
    st.divider()
    st.markdown('### Scoring Weights')
    st.markdown('- Revenue Growth: 20%')
    st.markdown('- EBITDA Margin: 20%')
    st.markdown('- Debt Ratio: 15%')
    st.markdown('- P/E Ratio: 15%')
    st.markdown('- ROE: 15%')
    st.markdown('- Current Ratio: 15%')
    st.divider()
    st.markdown('### DCF Assumptions')
    st.markdown('- WACC: 10%')
    st.markdown('- Terminal Growth: 2.5%')
    st.markdown('- Projection: 5 Years')
 
# ── Header ─────────────────────────────────────────────────────
st.title('📊 AI-Powered M&A Target Screener & Valuation Engine')
st.caption('Live financial data from Yahoo Finance  |  DCF valuation  |  Professional deal memos  |  No paid API required')
st.divider()
 
# ── Run button ──────────────────────────────────────────────────
if st.button('🚀 Run Full M&A Analysis', type='primary', use_container_width=True):
    with st.spinner('Step 1/3 — Downloading live financial data for 40+ companies from Yahoo Finance...'):
        df = run_screening()
        st.session_state['df'] = df
    with st.spinner('Step 2/3 — Running DCF valuations (5-year model, 10% WACC)...'):
        dcf = value_top_targets(df)
        st.session_state['dcf'] = dcf
    with st.spinner('Step 3/3 — Generating professional deal memos...'):
        memos = generate_all_memos(df, dcf)
        st.session_state['memos'] = memos
    st.success('✅ Analysis complete! Scroll down to explore results.')
 
# ── Results ─────────────────────────────────────────────────────
if 'df' in st.session_state:
    df  = st.session_state['df']
    dcf = st.session_state.get('dcf', [])
 
    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Companies Analysed', len(df))
    c2.metric('Top Score',  f"{df['ma_score'].max()}/100")
    c3.metric('Avg Score',  f"{df['ma_score'].mean():.1f}")
    c4.metric('#1 Target',  df.iloc[0]['company'][:18])
    c5.metric('Data Source', 'Yahoo Finance')
    st.divider()
 
    # Tab layout
    tab1, tab2, tab3, tab4 = st.tabs(['📈 Rankings', '💰 DCF Valuation', '📝 Deal Memos', '🗂 Full Data'])
 
    with tab1:
        st.subheader('Top 15 M&A Targets by Attractiveness Score')
        fig = px.bar(df.head(15), x='ma_score', y='company', orientation='h',
                     color='ma_score', color_continuous_scale='Blues',
                     labels={'ma_score': 'M&A Score', 'company': 'Company'},
                     hover_data=['sector', 'country', 'market_cap_bn'])
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=520)
        st.plotly_chart(fig, use_container_width=True)
 
        # Sector breakdown
        st.subheader('Score Distribution by Sector')
        sector_avg = df.groupby('sector')['ma_score'].mean().sort_values(ascending=False).reset_index()
        fig2 = px.bar(sector_avg, x='sector', y='ma_score', color='ma_score',
                      color_continuous_scale='Viridis',
                      labels={'ma_score': 'Avg M&A Score', 'sector': 'Sector'})
        st.plotly_chart(fig2, use_container_width=True)
 
    with tab2:
        st.subheader('DCF Valuation — Top 5 Targets')
        if dcf:
            dcf_rows = []
            for d in dcf:
                dcf_rows.append({
                    'Company':           d['company'],
                    'Market Cap ($B)':   d['market_cap_bn'],
                    'DCF Value ($B)':    d['dcf_value_bn'],
                    'Premium/Discount':  f"{d['dcf_premium_pct']:+.1f}%",
                    'PV FCFs ($B)':      d['pv_fcfs_bn'],
                    'PV Terminal ($B)':  d['pv_terminal_bn'],
                    'Terminal %':        f"{d['terminal_pct']:.0f}%",
                    'Growth Used':       f"{d['growth_used_pct']:.1f}%",
                    'M&A Score':         d['ma_score'],
                })
            st.dataframe(pd.DataFrame(dcf_rows), use_container_width=True)
 
            # Waterfall chart for first company
            d0 = dcf[0]
            fig3 = go.Figure(go.Waterfall(
                name='DCF Breakdown',
                orientation='v',
                x=['PV of FCFs', 'Terminal Value', 'Total DCF Value'],
                measure=['relative', 'relative', 'total'],
                y=[d0['pv_fcfs_bn'], d0['pv_terminal_bn'], 0],
                connector={'line': {'color': 'rgb(63, 63, 63)'}},
            ))
            fig3.update_layout(title=f"DCF Breakdown: {d0['company']}", height=380)
            st.plotly_chart(fig3, use_container_width=True)
 
    with tab3:
        st.subheader('Professional Deal Memos (Generated from Yahoo Finance Data)')
        if 'memos' in st.session_state:
            for ticker, data in st.session_state['memos'].items():
                with st.expander(f"📄 {data['company']} — Score: {data['score']}/100"):
                    st.code(data['memo'], language=None)
 
    with tab4:
        st.subheader('All Companies — Full Data Table')
        cols = ['rank','company','sector','country','market_cap_bn','revenue_bn',
                'revenue_growth_pct','ebitda_margin_pct','pe_ratio',
                'debt_to_equity','roe_pct','current_ratio','ma_score']
        st.dataframe(df[[c for c in cols if c in df.columns]].head(40),
                     use_container_width=True)
        # Download
        csv = df.to_csv(index=False)
        st.download_button('⬇️ Download Full Data as CSV', csv, 'ma_screener_results.csv', 'text/csv')

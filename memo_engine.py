# memo_engine.py
# Generates professional M&A deal memos from real Yahoo Finance data
# No AI API required — uses financial logic and structured templates
 
import pandas as pd
 
 
def classify_metric(value, thresholds, labels):
    """Map a numeric value to a qualitative label using thresholds."""
    if pd.isna(value):
        return 'Not Available'
    for threshold, label in zip(thresholds, labels):
        if value >= threshold:
            return label
    return labels[-1]
 
 
def generate_memo(row_dict, dcf):
    """
    Build a complete 6-section M&A investment memo.
    Uses only data already pulled from Yahoo Finance — no external API.
    """
    company  = row_dict.get('company', 'Unknown')
    sector   = row_dict.get('sector',  'Unknown')
    country  = row_dict.get('country', 'Unknown')
    mcap     = row_dict.get('market_cap_bn', 0) or 0
    rev      = row_dict.get('revenue_bn',    0) or 0
    rev_g    = row_dict.get('revenue_growth', None)
    ebitda_m = row_dict.get('ebitda_margin',  None)
    pe       = row_dict.get('pe_ratio',       None)
    de       = row_dict.get('debt_to_equity', None)
    roe      = row_dict.get('roe',            None)
    fcf      = row_dict.get('free_cash_flow_bn', 0) or 0
    score    = row_dict.get('ma_score',       0)
    beta     = row_dict.get('beta',           None)
 
    dcf_val  = dcf.get('dcf_value_bn', 0)
    dcf_prem = dcf.get('dcf_premium_pct', 0)
    growth_u = dcf.get('growth_used_pct', 3)
    disc_r   = int(dcf.get('discount_rate', 0.10) * 100)
 
    # === Qualitative assessments ===
    growth_q = classify_metric(rev_g,    [0.20, 0.10, 0.05, 0], ['High-Growth', 'Solid-Growth', 'Moderate-Growth', 'Low-Growth', 'Declining Revenue'])
    margin_q = classify_metric(ebitda_m, [0.30, 0.20, 0.10, 0], ['Best-in-Class Margins', 'Strong Margins', 'Adequate Margins', 'Thin Margins', 'EBITDA Negative'])
    debt_q   = classify_metric(-1*(de or 999), [-30, -60, -100, -150], ['Conservative Leverage', 'Moderate Leverage', 'Elevated Leverage', 'High Leverage', 'Overleveraged'])
    score_q  = classify_metric(score, [80, 65, 50, 35], ['Exceptional', 'Strong', 'Above Average', 'Average', 'Below Average'])
    dcf_q    = 'Undervalued' if dcf_prem > 20 else 'Fairly Valued' if dcf_prem > -10 else 'Overvalued'
    recco    = 'STRONG BUY' if score >= 75 else 'BUY' if score >= 60 else 'HOLD' if score >= 45 else 'AVOID'
 
    lines = []
    lines.append(f'INVESTMENT MEMO — {company.upper()}')
    lines.append(f'Sector: {sector}  |  Country: {country}  |  M&A Score: {score}/100 ({score_q})')
    lines.append('=' * 68)
    lines.append('')
    lines.append('1. INVESTMENT THESIS')
    lines.append('-' * 40)
    rev_g_str = f'{rev_g*100:.1f}%' if pd.notna(rev_g) else 'N/A'
    ebitda_str = f'{ebitda_m*100:.1f}%' if pd.notna(ebitda_m) else 'N/A'
    lines.append(f'{company} represents a {score_q.lower()} M&A opportunity in the {sector} sector,')
    lines.append(f'demonstrating {growth_q.lower()} at {rev_g_str} with {margin_q.lower()} at {ebitda_str} EBITDA margin.')
    lines.append(f'At a market capitalisation of ${mcap:.1f}B, the company offers {dcf_q.lower()} relative')
    lines.append(f'to our DCF intrinsic value estimate of ${dcf_val:.1f}B ({dcf_prem:+.1f}% premium/discount).')
    lines.append('')
    lines.append('2. STRATEGIC RATIONALE')
    lines.append('-' * 40)
    lines.append(f'  • {growth_q}: Revenue growing at {rev_g_str} — above the sector median,')
    lines.append(f'    indicating strong organic demand and market share expansion.')
    lines.append(f'  • {margin_q}: EBITDA margin of {ebitda_str} demonstrates operational')
    lines.append(f'    efficiency and sustainable profitability under an acquirer.')
    lines.append(f'  • {debt_q}: Debt/Equity of {de:.1f} provides financing headroom' if pd.notna(de) else '  • Leverage data unavailable — further due diligence required.')
    lines.append(f'    for a leveraged acquisition structure.')
    lines.append('')
    lines.append('3. FINANCIAL HIGHLIGHTS')
    lines.append('-' * 40)
    lines.append(f'  • Market Cap: ${mcap:.1f}B  |  Revenue (TTM): ${rev:.1f}B  |  Free Cash Flow: ${fcf:.2f}B')
    pe_str  = f'{pe:.1f}x' if pd.notna(pe) else 'N/A'
    roe_str = f'{roe*100:.1f}%' if pd.notna(roe) else 'N/A'
    lines.append(f'  • P/E Ratio: {pe_str}  |  Return on Equity: {roe_str}  |  Debt/Equity: {de:.1f}' if pd.notna(de) else f'  • P/E: {pe_str}  |  ROE: {roe_str}')
    lines.append(f'  • Beta: {beta:.2f} — ' + ('defensive, lower market risk' if (beta or 1) < 0.8 else 'moderate market correlation' if (beta or 1) < 1.2 else 'higher volatility, cyclical exposure') if pd.notna(beta) else '  • Beta: not available')
    lines.append('')
    lines.append('4. KEY RISKS')
    lines.append('-' * 40)
    lines.append(f'  • Integration Risk: Acquiring a {sector} company of ${mcap:.0f}B scale requires')
    lines.append(f'    significant management bandwidth and cultural alignment post-close.')
    if pd.notna(de) and de > 100:
        lines.append(f'  • Leverage Risk: D/E of {de:.1f} limits the acquirer credit rating headroom')
        lines.append(f'    and may require equity issuance to finance the deal.')
    elif pd.notna(beta) and beta > 1.3:
        lines.append(f'  • Macro Risk: Beta of {beta:.2f} implies above-average sensitivity to')
        lines.append(f'    economic downturns which may compress valuations at deal close.')
    else:
        lines.append(f'  • Valuation Risk: At ${mcap:.0f}B market cap, a control premium of 25–35%')
        lines.append(f'    typical in {sector} M&A would imply a deal value of ${mcap*1.30:.0f}–{mcap*1.35:.0f}B.')
    lines.append('')
    lines.append('5. VALUATION SUMMARY')
    lines.append('-' * 40)
    lines.append(f'DCF Analysis (10% WACC, {growth_u:.1f}% growth, 2.5% terminal rate, 5-year horizon):')
    lines.append(f'  PV of FCFs (Years 1–5):  ${dcf.get("pv_fcfs_bn", 0):.2f}B')
    lines.append(f'  PV of Terminal Value:    ${dcf.get("pv_terminal_bn", 0):.2f}B  ({dcf.get("terminal_pct",0):.0f}% of total)')
    lines.append(f'  Total Intrinsic Value:   ${dcf_val:.2f}B')
    lines.append(f'  vs. Market Cap:          ${mcap:.2f}B  →  {dcf_prem:+.1f}% ({dcf_q})')
    lines.append('')
    lines.append('6. RECOMMENDATION')
    lines.append('-' * 40)
    rec_reason = {
        'STRONG BUY': f'M&A Score of {score}/100 and DCF upside of {dcf_prem:.1f}% justify immediate target evaluation.',
        'BUY':        f'Solid fundamentals and {dcf_q.lower()} DCF support adding to acquisition pipeline.',
        'HOLD':       f'Mixed signals — monitor for improved growth or valuation reset before advancing.',
        'AVOID':      f'Weak financial metrics or overvalued — do not prioritise in current pipeline.',
    }
    lines.append(f'  >>> {recco} — {rec_reason[recco]}')
    lines.append('')
    lines.append('Data Source: Yahoo Finance (finance.yahoo.com) — pulled live at time of analysis.')
    lines.append('Model: Standard 5-year DCF with Gordon Growth terminal value.')
 
    return ' '.join(lines)
 
 
def generate_all_memos(df, dcf_results):
    """Generate a memo for each top target. Returns dict keyed by ticker."""
    print()
    print('Generating Deal Memos...')
    memos = {}
    top   = df[df['is_top_target']]
 
    for _, row in top.iterrows():
        dcf = next((d for d in dcf_results if d['company'] == row['company']), {})
        if dcf:
            print(f'  Memo: {row["company"]}...')
            memo = generate_memo(row.to_dict(), dcf)
            memos[row['ticker']] = {
                'company': row['company'],
                'memo':    memo,
                'score':   row['ma_score'],
                'dcf':     dcf,
            }
 
    return memos

# config.py
# Defines every company, scoring weights, and DCF parameters
 
IRISH_UK_COMPANIES = {
    'AIB.IR':   'AIB Group Ireland',
    'BIRG.IR':  'Bank of Ireland',
    'CRH':      'CRH plc',
    'KYGA.IR':  'Kerry Group',
    'ULVR.L':   'Unilever UK',
    'SHEL.L':   'Shell plc',
    'HSBA.L':   'HSBC Holdings',
    'AZN.L':    'AstraZeneca',
    'GSK.L':    'GSK plc',
    'BP.L':     'BP plc',
}
 
EUROPEAN_COMPANIES = {
    'SAP':       'SAP SE Germany',
    'ASML':      'ASML Netherlands',
    'SIE.DE':    'Siemens Germany',
    'ALV.DE':    'Allianz Germany',
    'OR.PA':     'LOreal France',
    'TTE.PA':    'TotalEnergies France',
    'NOVO-B.CO': 'Novo Nordisk Denmark',
    'NESN.SW':   'Nestle Switzerland',
    'ROG.SW':    'Roche Switzerland',
    'MC.PA':     'LVMH France',
}
 
US_COMPANIES = {
    'AAPL': 'Apple Inc',
    'MSFT': 'Microsoft',
    'GOOGL':'Alphabet Google',
    'AMZN': 'Amazon',
    'META': 'Meta Platforms',
    'JPM':  'JPMorgan Chase',
    'GS':   'Goldman Sachs',
    'BAC':  'Bank of America',
    'JNJ':  'Johnson and Johnson',
    'PFE':  'Pfizer',
    'KO':   'Coca-Cola',
    'PG':   'Procter and Gamble',
    'WMT':  'Walmart',
    'V':    'Visa Inc',
    'MA':   'Mastercard',
}
 
ASIA_COMPANIES = {
    'TSM':  'Taiwan Semiconductor',
    'SONY': 'Sony Group',
    'TM':   'Toyota Motor',
    'BABA': 'Alibaba Group',
}
 
ALL_COMPANIES = {}
ALL_COMPANIES.update(IRISH_UK_COMPANIES)
ALL_COMPANIES.update(EUROPEAN_COMPANIES)
ALL_COMPANIES.update(US_COMPANIES)
ALL_COMPANIES.update(ASIA_COMPANIES)
 
SCORING_WEIGHTS = {
    'revenue_growth': 0.20,
    'ebitda_margin':  0.20,
    'debt_ratio':     0.15,
    'pe_ratio':       0.15,
    'roe':            0.15,
    'current_ratio':  0.15,
}
 
DCF_SETTINGS = {
    'discount_rate':    0.10,   # 10% WACC — standard IB assumption
    'terminal_growth':  0.025,  # 2.5% perpetual growth
    'projection_years': 5,
    'growth_haircut':   0.70,   # Apply 30% haircut to stated growth
}
 
TOP_TARGETS  = 5
OUTPUT_FILE  = 'outputs/ma_report.xlsx'
# screener.py
# Downloads live financial data from Yahoo Finance and scores each company
 
import yfinance as yf
import pandas as pd
import time
from config import ALL_COMPANIES, SCORING_WEIGHTS, TOP_TARGETS
 


def get_financial_data(ticker, company_name):
    """Pull all required fields from Yahoo Finance. Returns dict or None."""
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info
 
        # Validate — skip if Yahoo returned an empty shell
        if not info.get('regularMarketPrice') and not info.get('marketCap'):
            print(f'  [skip] {ticker}: no market data returned')
            return None
 
        return {
            'ticker':             ticker,
            'company':            company_name,
            'sector':             info.get('sector',          'Unknown'),
            'industry':           info.get('industry',         'Unknown'),
            'country':            info.get('country',          'Unknown'),
            'currency':           info.get('currency',         'USD'),
            'market_cap_bn':      round(info.get('marketCap',       0) / 1e9, 2),
            'revenue_bn':         round(info.get('totalRevenue',    0) / 1e9, 2),
            'ebitda_bn':          round(info.get('ebitda',          0) / 1e9, 2),
            'revenue_growth':     info.get('revenueGrowth',    None),
            'earnings_growth':    info.get('earningsGrowth',   None),
            'ebitda_margin':      info.get('ebitdaMargins',    None),
            'gross_margin':       info.get('grossMargins',     None),
            'profit_margin':      info.get('profitMargins',    None),
            'pe_ratio':           info.get('trailingPE',       None),
            'forward_pe':         info.get('forwardPE',        None),
            'price_to_book':      info.get('priceToBook',      None),
            'ev_to_ebitda':       info.get('enterpriseToEbitda', None),
            'debt_to_equity':     info.get('debtToEquity',     None),
            'current_ratio':      info.get('currentRatio',     None),
            'quick_ratio':        info.get('quickRatio',       None),
            'roe':                info.get('returnOnEquity',   None),
            'roa':                info.get('returnOnAssets',   None),
            'free_cash_flow_bn':  round(info.get('freeCashflow',   0) / 1e9, 2),
            'operating_cf_bn':    round(info.get('operatingCashflow', 0) / 1e9, 2),
            'total_debt_bn':      round(info.get('totalDebt',       0) / 1e9, 2),
            'cash_bn':            round(info.get('totalCash',       0) / 1e9, 2),
            'employees':          info.get('fullTimeEmployees', None),
            '52w_high':           info.get('fiftyTwoWeekHigh',  None),
            '52w_low':            info.get('fiftyTwoWeekLow',   None),
            'beta':               info.get('beta',              None),
        }
    except Exception as e:
        print(f'  [error] {ticker}: {e}')
        return None
 
 
def score_company(row):
    """Calculate 0-100 M&A attractiveness score based on 6 weighted metrics."""
    score = 0
    w = SCORING_WEIGHTS
 
    # 1. Revenue growth (higher = better organic momentum)
    if pd.notna(row['revenue_growth']):
        g  = row['revenue_growth']
        gs = 100 if g > 0.20 else 75 if g > 0.10 else 50 if g > 0.05 else 25 if g > 0 else 0
        score += w['revenue_growth'] * gs
 
    # 2. EBITDA margin (higher = more profitable and easier to integrate)
    if pd.notna(row['ebitda_margin']):
        m  = row['ebitda_margin']
        ms = 100 if m > 0.30 else 75 if m > 0.20 else 50 if m > 0.10 else 25 if m > 0 else 0
        score += w['ebitda_margin'] * ms
 
    # 3. Debt ratio (lower debt = easier acquisition financing)
    if pd.notna(row['debt_to_equity']):
        d  = row['debt_to_equity']
        ds = 100 if d < 30 else 75 if d < 60 else 50 if d < 100 else 25 if d < 150 else 0
        score += w['debt_ratio'] * ds
 
    # 4. P/E ratio (lower = relatively cheaper target)
    if pd.notna(row['pe_ratio']) and row['pe_ratio'] > 0:
        pe = row['pe_ratio']
        ps = 100 if pe < 10 else 80 if pe < 15 else 60 if pe < 25 else 30 if pe < 35 else 10
        score += w['pe_ratio'] * ps
 
    # 5. ROE (higher = management generates more return for shareholders)
    if pd.notna(row['roe']):
        r  = row['roe']
        rs = 100 if r > 0.25 else 75 if r > 0.15 else 50 if r > 0.08 else 25 if r > 0 else 0
        score += w['roe'] * rs
 
    # 6. Current ratio (1.5–3.0 is ideal — liquid but not over-capitalised)
    if pd.notna(row['current_ratio']):
        cr = row['current_ratio']
        cs = 100 if 1.5 <= cr <= 3.0 else 70 if cr >= 3.0 else 60 if cr >= 1.0 else 20
        score += w['current_ratio'] * cs
 
    return round(score, 1)
 
 
def run_screening():
    """Main function — pull data for all companies, score, rank, and return DataFrame."""
    print('=' * 60)
    print('  M&A SCREENING ENGINE — Yahoo Finance Live Data')
    print('=' * 60)
    print(f'Analysing {len(ALL_COMPANIES)} companies. Estimated time: 4–6 minutes.')
    print('Data source: finance.yahoo.com (free, no API key required)')
    print()
 
    results = []
    failed  = []
 
    for i, (ticker, name) in enumerate(ALL_COMPANIES.items(), 1):
        print(f'  [{i:02}/{len(ALL_COMPANIES)}] Fetching: {name} ({ticker})...')
        data = get_financial_data(ticker, name)
        if data:
            results.append(data)
        else:
            failed.append(ticker)
        time.sleep(1.2)  # Polite delay — avoids Yahoo rate-limiting
 
    print()
    print(f'Fetched: {len(results)} companies | Skipped: {len(failed)}')
    if failed:
        print(f'Skipped tickers: {failed}')
 
    df = pd.DataFrame(results)
    df['ma_score'] = df.apply(score_company, axis=1)
    df = df.sort_values('ma_score', ascending=False).reset_index(drop=True)
    df['rank']          = df.index + 1
    df['is_top_target'] = df['rank'] <= TOP_TARGETS
 
    # Format percentage columns for display
    for col, label in [('revenue_growth','revenue_growth_pct'),
                       ('ebitda_margin', 'ebitda_margin_pct'),
                       ('roe',           'roe_pct'),
                       ('profit_margin', 'profit_margin_pct')]:
        df[label] = df[col].apply(lambda x: f'{x*100:.1f}%' if pd.notna(x) else 'N/A')
 
    print()
    print(f'TOP {TOP_TARGETS} M&A TARGETS:')
    for _, row in df[df['is_top_target']].iterrows():
        print(f'  #{int(row["rank"])}  {row["company"]:30s}  Score: {row["ma_score"]}/100  |  MCap: ${row["market_cap_bn"]}B')
 
    return df
# valuation.py
# 5-year DCF valuation model for each top M&A target
# All inputs sourced from Yahoo Finance via screener.py
 
import pandas as pd
from config import DCF_SETTINGS
 
 
def run_dcf(company_name, current_fcf_bn, revenue_growth):
    """
    Standard 5-year DCF with Gordon Growth terminal value.
    Returns a dict of all valuation components.
    """
    s      = DCF_SETTINGS
    r      = s['discount_rate']      # 10% WACC
    g_t    = s['terminal_growth']     # 2.5% perpetual growth
    years  = s['projection_years']    # 5 years
 
    # Conservative growth rate: haircut stated growth, cap at 25%
    if pd.isna(revenue_growth) or revenue_growth <= 0:
        growth = 0.03                # Default 3% if no positive growth data
    else:
        growth = min(revenue_growth * s['growth_haircut'], 0.25)
 
    # Default FCF if Yahoo data is missing or negative
    if pd.isna(current_fcf_bn) or current_fcf_bn <= 0:
        current_fcf_bn = 0.50        # $500m conservative floor
 
    # === Project 5 years of free cash flows ===
    fcfs = []
    fcf  = current_fcf_bn
    for yr in range(1, years + 1):
        fcf = fcf * (1 + growth)
        fcfs.append({'year': yr, 'fcf_bn': round(fcf, 3)})
 
    # === Discount each year back to present value ===
    pv_fcfs = []
    for item in fcfs:
        pv = item['fcf_bn'] / ((1 + r) ** item['year'])
        pv_fcfs.append(round(pv, 3))
 
    sum_pv_fcfs = sum(pv_fcfs)
 
    # === Terminal value — Gordon Growth Model ===
    terminal_value = fcfs[-1]['fcf_bn'] * (1 + g_t) / (r - g_t)
    pv_terminal    = terminal_value / ((1 + r) ** years)
 
    intrinsic_value = sum_pv_fcfs + pv_terminal
 
    return {
        'company':          company_name,
        'dcf_value_bn':     round(intrinsic_value, 2),
        'pv_fcfs_bn':       round(sum_pv_fcfs, 2),
        'pv_terminal_bn':   round(pv_terminal, 2),
        'terminal_pct':     round(pv_terminal / intrinsic_value * 100, 1),
        'growth_used_pct':  round(growth * 100, 1),
        'discount_rate':    r,
        'projected_fcfs':   fcfs,
        'pv_fcfs':          pv_fcfs,
    }
 
 
def value_top_targets(df):
    """Run DCF for each top target and compute premium/discount to market cap."""
    print()
    print('Running DCF Valuations...')
    dcf_results = []
 
    for _, row in df[df['is_top_target']].iterrows():
        print(f'  DCF: {row["company"]}...')
        result = run_dcf(
            row['company'],
            row['free_cash_flow_bn'],
            row['revenue_growth']
        )
        result['market_cap_bn']  = row['market_cap_bn']
        result['ma_score']       = row['ma_score']
        result['sector']         = row['sector']
        result['country']        = row['country']
        result['ev_to_ebitda']   = row.get('ev_to_ebitda', None)
        result['pe_ratio']       = row.get('pe_ratio', None)
 
        # Premium = how much DCF value exceeds current market cap (% upside)
        mcap = row['market_cap_bn']
        if mcap and mcap > 0:
            result['dcf_premium_pct'] = round(
                (result['dcf_value_bn'] - mcap) / mcap * 100, 1
            )
        else:
            result['dcf_premium_pct'] = 0
 
        dcf_results.append(result)
 
    return dcf_results

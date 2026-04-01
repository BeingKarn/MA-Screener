import yfinance as yf
import pandas as pd
import time
from config import ALL_COMPANIES, SCORING_WEIGHTS, TOP_TARGETS


def safe_float(value):
    """Safely convert value to float, return NaN if invalid."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return pd.NA


def get_financial_data(ticker, company_name):
    """Pull all required fields from Yahoo Finance. Returns dict or None."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info.get('regularMarketPrice') and not info.get('marketCap'):
            print(f'  [skip] {ticker}: no market data returned')
            return None

        return {
            'ticker': ticker,
            'company': company_name,
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'country': info.get('country', 'Unknown'),
            'currency': info.get('currency', 'USD'),

            'market_cap_bn': safe_float(info.get('marketCap', 0)) / 1e9,
            'revenue_bn': safe_float(info.get('totalRevenue', 0)) / 1e9,
            'ebitda_bn': safe_float(info.get('ebitda', 0)) / 1e9,

            'revenue_growth': safe_float(info.get('revenueGrowth')),
            'earnings_growth': safe_float(info.get('earningsGrowth')),
            'ebitda_margin': safe_float(info.get('ebitdaMargins')),
            'gross_margin': safe_float(info.get('grossMargins')),
            'profit_margin': safe_float(info.get('profitMargins')),

            'pe_ratio': safe_float(info.get('trailingPE')),
            'forward_pe': safe_float(info.get('forwardPE')),
            'price_to_book': safe_float(info.get('priceToBook')),
            'ev_to_ebitda': safe_float(info.get('enterpriseToEbitda')),

            'debt_to_equity': safe_float(info.get('debtToEquity')),
            'current_ratio': safe_float(info.get('currentRatio')),
            'quick_ratio': safe_float(info.get('quickRatio')),

            'roe': safe_float(info.get('returnOnEquity')),
            'roa': safe_float(info.get('returnOnAssets')),

            'free_cash_flow_bn': safe_float(info.get('freeCashflow', 0)) / 1e9,
            'operating_cf_bn': safe_float(info.get('operatingCashflow', 0)) / 1e9,
            'total_debt_bn': safe_float(info.get('totalDebt', 0)) / 1e9,
            'cash_bn': safe_float(info.get('totalCash', 0)) / 1e9,

            'employees': safe_float(info.get('fullTimeEmployees')),
            '52w_high': safe_float(info.get('fiftyTwoWeekHigh')),
            '52w_low': safe_float(info.get('fiftyTwoWeekLow')),
            'beta': safe_float(info.get('beta')),
        }

    except Exception as e:
        print(f'  [error] {ticker}: {e}')
        return None


def score_company(row):
    """Calculate 0-100 M&A attractiveness score."""
    score = 0
    w = SCORING_WEIGHTS

    # 1. Revenue growth
    g = row['revenue_growth']
    if pd.notna(g):
        gs = 100 if g > 0.20 else 75 if g > 0.10 else 50 if g > 0.05 else 25 if g > 0 else 0
        score += w['revenue_growth'] * gs

    # 2. EBITDA margin
    m = row['ebitda_margin']
    if pd.notna(m):
        ms = 100 if m > 0.30 else 75 if m > 0.20 else 50 if m > 0.10 else 25 if m > 0 else 0
        score += w['ebitda_margin'] * ms

    # 3. Debt ratio
    d = row['debt_to_equity']
    if pd.notna(d):
        ds = 100 if d < 30 else 75 if d < 60 else 50 if d < 100 else 25 if d < 150 else 0
        score += w['debt_ratio'] * ds

    # 4. P/E ratio (SAFE now)
    pe = row['pe_ratio']
    if pd.notna(pe) and isinstance(pe, (int, float)) and pe > 0:
        ps = 100 if pe < 10 else 80 if pe < 15 else 60 if pe < 25 else 30 if pe < 35 else 10
        score += w['pe_ratio'] * ps

    # 5. ROE
    r = row['roe']
    if pd.notna(r):
        rs = 100 if r > 0.25 else 75 if r > 0.15 else 50 if r > 0.08 else 25 if r > 0 else 0
        score += w['roe'] * rs

    # 6. Current ratio
    cr = row['current_ratio']
    if pd.notna(cr):
        cs = 100 if 1.5 <= cr <= 3.0 else 70 if cr >= 3.0 else 60 if cr >= 1.0 else 20
        score += w['current_ratio'] * cs

    return round(score, 1)


def clean_dataframe(df):
    """Ensure all numeric columns are properly typed."""
    numeric_cols = [
        'market_cap_bn','revenue_bn','ebitda_bn','revenue_growth','earnings_growth',
        'ebitda_margin','gross_margin','profit_margin','pe_ratio','forward_pe',
        'price_to_book','ev_to_ebitda','debt_to_equity','current_ratio',
        'quick_ratio','roe','roa','free_cash_flow_bn','operating_cf_bn',
        'total_debt_bn','cash_bn','employees','52w_high','52w_low','beta'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def run_screening():
    print('=' * 60)
    print('  M&A SCREENING ENGINE — Yahoo Finance Live Data')
    print('=' * 60)
    print(f'Analysing {len(ALL_COMPANIES)} companies. Estimated time: 4–6 minutes.\n')

    results = []
    failed = []

    for i, (ticker, name) in enumerate(ALL_COMPANIES.items(), 1):
        print(f' [{i:02}/{len(ALL_COMPANIES)}] Fetching: {name} ({ticker})...')
        data = get_financial_data(ticker, name)

        if data:
            results.append(data)
        else:
            failed.append(ticker)

        time.sleep(1.2)

    print(f'\nFetched: {len(results)} | Skipped: {len(failed)}')

    df = pd.DataFrame(results)

    # 🔑 CRITICAL FIX: clean ALL data before scoring
    df = clean_dataframe(df)

    df['ma_score'] = df.apply(score_company, axis=1)
    df = df.sort_values('ma_score', ascending=False).reset_index(drop=True)

    df['rank'] = df.index + 1
    df['is_top_target'] = df['rank'] <= TOP_TARGETS

    # Format % columns safely
    for col, label in [
        ('revenue_growth','revenue_growth_pct'),
        ('ebitda_margin','ebitda_margin_pct'),
        ('roe','roe_pct'),
        ('profit_margin','profit_margin_pct')
    ]:
        df[label] = df[col].apply(
            lambda x: f'{x*100:.1f}%' if pd.notna(x) else 'N/A'
        )

    print(f'\nTOP {TOP_TARGETS} M&A TARGETS:')
    for _, row in df[df['is_top_target']].iterrows():
        print(
            f'  #{int(row["rank"])} {row["company"]:30s} '
            f'Score: {row["ma_score"]}/100 | MCap: ${row["market_cap_bn"]:.2f}B'
        )

    return df
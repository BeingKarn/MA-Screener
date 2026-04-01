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

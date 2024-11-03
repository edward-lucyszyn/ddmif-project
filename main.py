import wrds
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as si
from scipy import optimize
import statsmodels.api as sm

from functions.plot import *
from functions.correlation import *
from functions.co_integration import *
from functions.spread import *
from functions.trading_signals import *

# https://wrds-www.wharton.upenn.edu/pages/wrds-research/applications/python-replications/historical-sp-500-index-constituents/

def get_dates(date, duration, duration_type):
    """
    Parameters
    ----------
    date : str
        The end date in the format 'YYYY-MM-DD'.
    duration : int
        The duration of the period.
    duration_type : str
        The type of duration. Choose from 'years', 'months', or 'days'.
        
    Returns
    -------
    start_date : datetime
        The start date of the period.
    end_date : datetime
        The end date of the period.
    """
    
    if not isinstance(date, str):
        raise ValueError('Date must be a string in the format YYYY-MM-DD.')
    end_date = pd.to_datetime(date)
    if duration_type == 'years':
        start_date = end_date - pd.DateOffset(years=duration)
    elif duration_type == 'months':
        start_date = end_date - pd.DateOffset(months=duration)
    elif duration_type == 'days':
        start_date = end_date - pd.DateOffset(days=duration)
    else:
        raise ValueError('Invalid duration type. Please choose from years, months, or days.')
    
    print(f'Start date: {start_date.strftime("%m/%d/%Y")}')
    print(f'End date: {end_date.strftime("%m/%d/%Y")}')
    return start_date, end_date


def get_data(start_date, end_date):
    """
    Parameters
    ----------
    start_date : datetime
        The start date of the period.
        end_date : datetime
        The end date of the period.
    
    Returns
    -------
    sp500ccm : DataFrame
        The S&P 500 data with company names and additional descriptive variables.
    """
    
    print('Extracting data...')
    
    # Extract S&P 500 data from CRSP
    sp500_query = f"""
    SELECT a.*, b.date, b.ret
    FROM crsp.msp500list AS a
    JOIN crsp.msf AS b ON a.permno = b.permno
    WHERE b.date >= a.start 
    AND b.date <= a.ending 
    AND b.date >= '01/01/2000'
    ORDER BY date;
    """
    sp500 = db.raw_sql(sp500_query, date_cols=['start', 'ending', 'date'])
    ## REVIEW line "AND b.date <= '{end_date.strftime('%m/%d/%Y')}'"
    
    # Add company names and additional descriptive data from CRSP's msenames
    mse_query = """
    SELECT comnam, ncusip, namedt, nameendt, permno, shrcd, exchcd, hsiccd, ticker
    FROM crsp.msenames;
    """
    mse = db.raw_sql(mse_query, date_cols=['namedt', 'nameendt'])
    
    # Replace missing 'nameendt' with today's date
    mse['nameendt'] = mse['nameendt'].fillna(pd.to_datetime('today'))
    
    # Merge S&P 500 data with descriptive variables (mse data)
    sp500_full = pd.merge(sp500, mse, how='left', on='permno')

    # Filter rows to ensure date range alignment between SP500 data and company names
    sp500_full = sp500_full[(sp500_full['date'] >= sp500_full['namedt']) & (sp500_full['date'] <= sp500_full['nameendt'])]

    # Extract Compustat linkage data (CCM)
    ccm_query = """
    SELECT gvkey, liid AS iid, lpermno AS permno, linktype, linkprim, linkdt, linkenddt
    FROM crsp.ccmxpf_linktable
    WHERE SUBSTR(linktype,1,1) = 'L' 
    AND (linkprim = 'C' OR linkprim = 'P');
    """
    ccm = db.raw_sql(ccm_query, date_cols=['linkdt', 'linkenddt'])

    # Replace missing 'linkenddt' with today's date
    ccm['linkenddt'] = ccm['linkenddt'].fillna(pd.to_datetime('today'))
    ## REVIEW line "ccm['linkenddt'] = ccm['linkenddt'].fillna(pd.to_datetime('today'))"

    # Merge CCM data with S&P500 data using PERMNO
    sp500ccm = pd.merge(sp500_full, ccm, how='left', on='permno')

    # Filter data based on link date range
    sp500ccm = sp500ccm[(sp500ccm['date'] >= sp500ccm['linkdt']) & 
                        (sp500ccm['date'] <= sp500ccm['linkenddt'])]

    # Drop unnecessary columns
    sp500ccm = sp500ccm.drop(columns=['namedt', 'nameendt', 'linktype', 'linkprim', 'linkdt'])

    # Rearrange columns for final output
    sp500ccm = sp500ccm[['date', 'permno', 'comnam', 'ncusip', 'shrcd', 'exchcd', 'hsiccd', 'ticker', 
                        'gvkey', 'iid', 'start', 'ending', 'ret', 'linkenddt']]

    sp500ccm['comnam'] = sp500ccm['comnam'].str.replace(' ', '_', regex=False)

    # Count the number of companies (permno) by date
    cnt = sp500ccm.groupby(['date'])['permno'].count().reset_index().rename(columns={'permno': 'npermno'})
    
    # Return the processed data (e.g., sample)
    print('Data extraction completed.')
    return sp500ccm


def calculate_return_stock(permno_SP500, start_date, end_date):
    # Get the list of permnos for the S&P 500 companies
    permno_list = permno_SP500['permno'].tolist()

    # Adjust the start_date to begin 10 days earlier
    start_date1 = pd.to_datetime(start_date) - pd.DateOffset(days=10)

    # SQL query to get stock prices between the adjusted start_date and end_date
    query = f"""
    SELECT date, permno, prc
        FROM crsp.dsf
        WHERE permno IN ({', '.join([str(p) for p in permno_list])})
        AND date >= '{start_date1}'
        AND date <= '{end_date}'
    """
   
    stock_prices = pd.DataFrame(db.raw_sql(query))
    stock_prices['date'] = pd.to_datetime(stock_prices['date'])

    # Pivot the data to have permno as columns and date as the index
    return_pivoted = stock_prices.pivot(index='date', columns='permno', values='prc')

    # Mapper permnos aux noms d'entreprises
    permno_to_name = permno_SP500.set_index('permno')['comnam'].to_dict()
    
    # Renommer les colonnes de 'prc_permno' à 'prc_nomdelentreprise'
    return_pivoted.columns = [f"prc_{permno_to_name[int(col)]}" for col in return_pivoted.columns]

    # Create a full range of dates between the start and end dates
    full_dates = pd.date_range(start=start_date1, end=end_date, freq='D')

    # Reindex the DataFrame to include all dates in the range, and fill missing values with the previous day's price
    return_pivoted = return_pivoted.reindex(full_dates).ffill()

    # Return the DataFrame starting from the actual start_date, keeping date as index
    return return_pivoted[return_pivoted.index >= start_date]




def start(date='2023-12-31', duration=10, duration_type='years', correlation_threshold=0.8, cointegration_threshold=0.05, z_score_threshold=0.3):
    
    # Get the start and end dates based on the input parameters
    start_date, end_date = get_dates(date, duration, duration_type)
    
    # Get the S&P 500 data with company names and additional descriptive variables
    sp500ccm = get_data(start_date, end_date)
    sp500ccm_current = sp500ccm[sp500ccm['date'] == sp500ccm['date'].max()]
    permno_SP500 = sp500ccm_current[['comnam', 'permno']]
    
    # Calculate the stock returns for the S&P 500 companies
    stock_prices_SP500 = calculate_return_stock(permno_SP500, start_date, end_date)
    
    # Plot pairs of stocks
    # plot_pair(stock_prices_SP500.columns[0], stock_prices_SP500.columns[1], stock_prices_SP500)
    
    # Calculate the daily returns
    returns = stock_prices_SP500.pct_change()
    returns.iloc[0] = 0
    
    # Example usage:
    # stock_symbol = 'prc_MICROSOFT_CORP'
    # plot_stock_and_returns(stock_prices_SP500, returns, stock_symbol)
    
    pairs = add_correlation(returns)
    pairs_correlated = select_high_correlation(pairs, threshold=correlation_threshold)
    pairs_correlated = add_test_cointegration_pairs(stock_prices_SP500, pairs_correlated)
    pairs_correlated_cointegrated = select_high_cointegration(pairs_correlated, threshold=cointegration_threshold)
    
    spreads = calculate_spreads_for_pairs(stock_prices_SP500, pairs_correlated_cointegrated)
    z_scores_for_spreads = calculate_z_scores_for_spreads(spreads)
    
    
if __name__ == '__main__':
    db = wrds.Connection()
    start()
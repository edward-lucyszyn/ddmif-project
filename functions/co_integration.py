import pandas as pd
import statsmodels.api as sm

def add_test_cointegration_pairs(stock_data, high_correlation_return):
    
    cointegrated_pairs = []

    # Loop over each pair of stocks from the high correlation DataFrame
    for _, row in high_correlation_return.iterrows():
        stock_1 = row['Stock 1']
        stock_2 = row['Stock 2']
        correlation = row['Correlation']

        # Get the stock price data for the two stocks
        stock_1_prices = stock_data[stock_1]
        stock_2_prices = stock_data[stock_2]
        
        # Drop rows where either stock has missing (NaN) values
        combined_data = pd.concat([stock_1_prices, stock_2_prices], axis=1).dropna()
        
        # Re-extract clean series
        stock_1_clean = combined_data.iloc[:, 0]
        stock_2_clean = combined_data.iloc[:, 1]

        # Perform the cointegration test on the clean data
        score, p_value, _ = sm.tsa.stattools.coint(stock_1_clean, stock_2_clean)

        cointegrated_pairs.append([stock_1, stock_2, correlation, p_value])

    # Create a DataFrame to store the results
    df_cointegration = pd.DataFrame(cointegrated_pairs, columns=['Stock 1', 'Stock 2', 'Correlation', 'P-Value'])
    
    # Sort by p-value in ascending order (lower p-values indicate stronger cointegration)
    df_cointegration.sort_values('P-Value', ascending=True, inplace=True)

    return df_cointegration


def select_high_cointegration(pairs_correlated, threshold=0.05):
    return pairs_correlated[pairs_correlated['P-Value'] <= threshold]
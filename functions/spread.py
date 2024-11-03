import pandas as pd
import statsmodels.api as sm
import numpy as np

def calculate_spread(stock_A, stock_B):

    # Combine the two stock series into a single DataFrame
    combined_data = pd.concat([stock_A, stock_B], axis=1)
    
    # Remove rows with NaN or infinite values
    combined_data.replace([np.inf, -np.inf], np.nan, inplace=True)
    combined_data = combined_data.dropna()

    # Extract clean stock prices
    stock_A_clean = combined_data.iloc[:, 0]
    stock_B_clean = combined_data.iloc[:, 1]

    # Perform linear regression of stock_A on stock_B to get the hedge ratio
    X = sm.add_constant(stock_B_clean)
    model = sm.OLS(stock_A_clean, X).fit()

    # Calculate the spread as the residual from the regression
    spread = stock_A_clean - model.predict(X)

    return spread


def calculate_spreads_for_pairs(stock_data, cointegrated_return):

    spreads_list = []  # Créer une liste pour stocker les DataFrames temporairement

    # Loop over each pair of cointegrated stocks
    for _, row in cointegrated_return.iterrows():
        stock_1 = row['Stock 1']
        stock_2 = row['Stock 2']
        
        # Get the price series for the two stocks
        stock_1_prices = stock_data[stock_1]
        stock_2_prices = stock_data[stock_2]
        
        # Calculate the spread using the calculate_spread function
        spread = calculate_spread(stock_1_prices, stock_2_prices)
        
        # Create a DataFrame for the spread
        spread_name = f'{stock_1}_vs_{stock_2}'
        temp_return = pd.DataFrame({spread_name: spread}, index=stock_data.index)
        
        # Add the spread DataFrame to the list
        spreads_list.append(temp_return)

    # Concatenate all the spread DataFrames into a single DataFrame
    spreads = pd.concat(spreads_list, axis=1)

    return spreads


def calculate_z_score(spread):

    mean_spread = spread.mean()
    std_spread = spread.std()

    z_score = (spread - mean_spread) / std_spread
    return z_score


def calculate_z_scores_for_spreads(spreads_return):

    z_scores = spreads_return.apply(calculate_z_score, axis=0)
    return z_scores


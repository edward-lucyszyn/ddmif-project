def add_correlation(stock_returns):

    # Calculate the correlation matrix
    correlation_matrix = stock_returns.corr()

    # Unstack the correlation matrix to create a Series of stock pairs and their correlations
    pair_correlations = correlation_matrix.unstack().reset_index()

    # Rename the columns
    pair_correlations.columns = ['Stock 1', 'Stock 2', 'Correlation']

    # Remove duplicates and self-correlations (correlation of a stock with itself)
    pair_correlations = pair_correlations[pair_correlations['Stock 1'] != pair_correlations['Stock 2']]

    # Optional: Sort the pairs by their correlation coefficient
    pair_correlations = pair_correlations.sort_values(by='Correlation', ascending=False).reset_index(drop=True)

    return pair_correlations


def select_high_correlation(correlation_pairs, threshold=0.8):

    # Filter pairs with correlation above the threshold
    high_correlation_pairs = correlation_pairs[correlation_pairs['Correlation'] > threshold]

    return high_correlation_pairs
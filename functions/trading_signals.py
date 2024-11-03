import pandas as pd
from spread import calculate_z_score

def generate_trading_signals(z_scores, entry_threshold=2, exit_threshold=1):

    signals = pd.Series(index=z_scores.index, dtype=float)

    for i in range(1, len(z_scores)):
        if z_scores.iloc[i] > entry_threshold:
            signals.iloc[i] = -1  # Short
        elif z_scores.iloc[i] < -entry_threshold:
            signals.iloc[i] = 1   # Long
        elif abs(z_scores.iloc[i]) < exit_threshold:
            signals.iloc[i] = 0   # Close the position (exit)
        else:
            signals.iloc[i] = signals.iloc[i-1]  # Hold the current position

    return pd.DataFrame(signals, columns=['Signal'])


def simulate_orders(stock_A, stock_B, entry_threshold=2, exit_threshold=1):

    spread = stock_A - stock_B

    z_scores = calculate_z_score(spread)

    signals = generate_trading_signals(z_scores, entry_threshold, exit_threshold)

    orders = pd.DataFrame(index=spread.index)
    
    orders['Stock_A_Order'] = 0
    orders['Stock_B_Order'] = 0

    for i in range(1, len(signals)):
        if signals.iloc[i]['Signal'] == 1:  # Long position
            orders.loc[orders.index[i], 'Stock_A_Order'] = 1  # Buy stock A
            orders.loc[orders.index[i], 'Stock_B_Order'] = -1  # Short stock B
        elif signals.iloc[i]['Signal'] == -1:  # Short position
            orders.loc[orders.index[i], 'Stock_A_Order'] = -1  # Short stock A
            orders.loc[orders.index[i], 'Stock_B_Order'] = 1  # Buy stock B
        elif signals.iloc[i]['Signal'] == 0:  # Exit position
            orders.loc[orders.index[i], 'Stock_A_Order'] = 0  # Exit both stocks
            orders.loc[orders.index[i], 'Stock_B_Order'] = 0

    return orders


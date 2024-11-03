import matplotlib.pyplot as plt

def plot_pair(stockA, stockB, stock_prices_SP500):
    
    plt.figure(figsize=(12, 8))
    plt.plot(stock_prices_SP500[stockA], label=stockA, linewidth=2)
    plt.plot(stock_prices_SP500[stockB], label=stockB, linewidth=2)
    plt.title(f'{stockA} vs. {stockB} Stock Prices', fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Stock Price', fontsize=12)
    plt.legend(loc='best')
    plt.grid(True)

    plt.savefig(f'outputs/{stockA}_{stockB}_stock_prices.png')
    plt.show()
    
    
def plot_stock_and_returns(stock_prices, returns, stock_symbol):

    # Create a figure and two subplots
    fig, ax1 = plt.subplots(figsize=(12, 8))

    # Plot stock prices on the first axis
    ax1.plot(stock_prices.index, stock_prices[stock_symbol], color='blue', label='Stock Price')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Stock Price', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # Create a second y-axis for returns
    ax2 = ax1.twinx()
    ax2.plot(returns.index, returns[stock_symbol], color='green', label='Daily Returns', linestyle='--')
    ax2.set_ylabel('Daily Returns', color='green')
    ax2.tick_params(axis='y', labelcolor='green')

    # Title and display the plot
    plt.title(f'{stock_symbol} Stock Price and Daily Returns')
    fig.tight_layout()
    plt.savefig(f'outputs/{stock_symbol}_stock_price_returns.png')
    plt.show()
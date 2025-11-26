import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from trading_bot.config import cfg

class Results:
    def __init__(self, trades, portfolio_history, initial_capital, risk_free_rate=0.0401):
        self.trades = pd.DataFrame(trades)
        self.portfolio_history = pd.DataFrame(portfolio_history)
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate

    def calculate_metrics(self):
        # Total Trades
        total_trades = len(self.trades)

        # Winning and Losing Trades
        winning_trades = self.trades[self.trades['pnl'] > 0]
        losing_trades = self.trades[self.trades['pnl'] <= 0]
        num_winning_trades = len(winning_trades)
        num_losing_trades = len(losing_trades)

        # Win/Loss Ratio
        win_loss_ratio = num_winning_trades / num_losing_trades if num_losing_trades > 0 else float('inf')

        # Max Profit and Loss
        max_profit = winning_trades['pnl'].max() if not winning_trades.empty else 0
        max_loss = losing_trades['pnl'].min() if not losing_trades.empty else 0

        # Average Profit and Loss
        avg_profit = winning_trades['pnl'].mean() if not winning_trades.empty else 0
        avg_loss = losing_trades['pnl'].mean() if not losing_trades.empty else 0
        
        # Equity Curve and Returns
        equity_curve = self.portfolio_history['portfolio_value']
        returns = equity_curve.pct_change().dropna()

        # Sharpe Ratio
        sharpe_ratio = self.calculate_sharpe_ratio(returns)

        # Max Drawdown
        max_drawdown = self.calculate_max_drawdown(equity_curve)

        return {
            'total_trades': total_trades,
            'num_winning_trades': num_winning_trades,
            'num_losing_trades': num_losing_trades,
            'win_loss_ratio': win_loss_ratio,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'final_portfolio_value': equity_curve.iloc[-1]
        }

    def calculate_sharpe_ratio(self, returns):
        # Determine the number of periods per year based on the configured timeframe
        minutes_in_year = 365 * 24 * 60
        periods_per_year = minutes_in_year / cfg.TIMEFRAME
        
        excess_returns = returns - (self.risk_free_rate / periods_per_year)
        
        # Check if std dev is zero
        if np.std(excess_returns) == 0:
            return 0.0
        
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(periods_per_year)
    
    def calculate_max_drawdown(self, equity_curve):
        peak = equity_curve.cummax()
        drawdown = (equity_curve - peak) / peak
        return drawdown.min()

    def generate_equity_curve(self, output_path='equity_curve.png'):
        plt.figure(figsize=(12, 6))
        plt.plot(self.portfolio_history['timestamp'], self.portfolio_history['portfolio_value'])
        plt.title('Equity Curve')
        plt.xlabel('Timestamp')
        plt.ylabel('Portfolio Value')
        plt.grid(True)
        plt.savefig(output_path)
        plt.close()

    def display_results(self, metrics):
        print("--- Backtesting Results ---")
        for key, value in metrics.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        print("---------------------------")

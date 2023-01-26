# -- Created by carlesferreres at 11/12/22 

# -- Built-in and installed packages
import math
import numpy as np
import pandas as pd
import plotly.express as px
# -- User custom function, classes and objects
from python.Logger import Logger


class PerformanceMetrics:
    YEARLY_TRADING_DAYS = 365

    def __init__(self, initial_capital, taker_fee):
        # Parameters
        self.initial_capital = initial_capital
        self.taker_fee = taker_fee

        # Logger
        self.logger = Logger('PerfMetr').get_logger()

    def get_metrics(self, results_df):
        try:
            self.metrics = {}
            self.compute_metrics(results_df)
            return self.metrics
        except Exception as e:
            self.logger.error(f'Error computing the metrics: {e}')

    def get_score(self, results_df):
        try:
            self.metrics = {}
            return self.compute_score(results_df)
        except Exception as e:
            self.logger.error(f'Error computing the score: {e}')

    def strategy_returns(self, results_df):
        # Calculate necessary fields for metrics
        results_df['log_ret'] = (np.log(results_df['close'] / results_df['close'].shift(1))).fillna(0)
        results_df['new_order'] = results_df.position != results_df.position.shift(1).fillna(0)
        results_df['s_log_ret'] = (results_df['position'].shift(1) * results_df['log_ret'] + \
                                   np.log(1 - self.taker_fee) * results_df['new_order'].shift(1)).fillna(0)
        results_df['cum_s_log_ret'] = results_df['s_log_ret'].cumsum()
        results_df['pnl'] = self.initial_capital * results_df['cum_s_log_ret'].apply(np.exp)

        # Metrics
        self.metrics['initial_capital'] = self.initial_capital
        self.metrics['pnl'] = round(results_df['pnl'].iloc[-1] - self.initial_capital, 2)
        self.metrics['strategy_ret'] = round((np.exp(results_df['s_log_ret'].sum()) - 1) * 100, 2)

    def buy_and_hold(self, results_df):
        # Calculate return of buy and hold strategy
        results_df['cum_log_ret'] = results_df['log_ret'].cumsum()
        self.metrics['bnh'] = round((np.exp(results_df['cum_log_ret'].iloc[-1] + np.log(1 - self.taker_fee)) - 1) * 100, 2)

    def max_dd(self, results_df):
        # Calculate cumulative log returns
        results_df['cum_s_log_ret'] = results_df['s_log_ret'].cumsum()

        # Calculate the maximum cumulative log returns
        results_df['max_cum_s_log_ret'] = results_df['cum_s_log_ret'].cummax()

        # Drawdown is the difference between max cumulative log returns and current log returns
        results_df['drawdown'] = (results_df['cum_s_log_ret'] - results_df['max_cum_s_log_ret'])

        # Get the maximum drawdown
        dd = {'max_dd_period': str(pd.to_datetime(results_df.loc[results_df['drawdown'] ==
                                                                 results_df['drawdown'].min()].index[0])),
              'max_dd_value': round((np.exp(results_df['drawdown'].min()) - 1) * 100, 2)}
        self.metrics['max_dd'] = dd

    def sharpe_ratio(self, results_df):
        # Calculate annualized sharpe ratio
        self.metrics['sharpe_ratio'] = round(results_df['s_log_ret'].mean() / \
                                             results_df['s_log_ret'].std() * \
                                             math.sqrt(self.YEARLY_TRADING_DAYS), 2)

    def number_of_trades(self, results_df):
        self.metrics['amount_of_trades'] = results_df['new_order'].sum()

    def win_rate(self):
        # TODO
        pass

    def calmar_ratio(self):
        # TODO
        pass

    def gain_to_pain_ratio(self):
        # TODO
        pass

    def profit_ratio(self):
        # TODO
        pass

    def compute_metrics(self, results_df):
        if isinstance(results_df, pd.DataFrame):
            self.strategy_returns(results_df)
            self.buy_and_hold(results_df)
            self.max_dd(results_df)
            self.sharpe_ratio(results_df)
            self.number_of_trades(results_df)
        else:
            self.logger.warning('Results dataframe is empty. Please, execute a strategy before computing metrics')
            return 0

    def compute_score(self, results_df):
        self.strategy_returns(results_df)
        return self.metrics['pnl']

    def plot_results(self, results_df, cols: list = None):
        try:
            if not cols:
                cols = ['cum_ret', 'cum_s_ret']
                results_df['cum_ret'] = results_df['log_ret'].cumsum().apply(np.exp) - 1
                results_df['cum_s_ret'] = results_df['s_log_ret'].cumsum().apply(np.exp) - 1
            fig = px.line(results_df[cols], x=results_df.index, y=cols)
            fig.show()
        except Exception as e:
            self.logger.error(f'Error plotting results: {e}')

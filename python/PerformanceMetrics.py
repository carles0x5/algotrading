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
        self.logger = Logger(self.__class__.__name__).logger

    # def get_score(self, results_df):
    #     try:
    #         self.metrics = {}
    #         return self.compute_score(results_df)
    #     except Exception as e:
    #         self.logger.error(f'Error computing the score: {e}')

    def _strategy_log_returns(self, df):
        # Calculate necessary fields for metrics
        df['log_ret'] = (np.log(df['close'] / df['close'].shift(1))).fillna(0)
        df['new_order'] = df.position != df.position.shift(1).fillna(0)
        df['s_log_ret'] = (df['position'].shift(1) * df['log_ret'] +
                           np.log(1 - self.taker_fee) * df['new_order'].shift(1)).fillna(0)
        return df.s_log_ret

    @staticmethod
    def _strategy_rate_of_return(df):
        s_returns = round((np.exp(df['s_log_ret'].sum()) - 1) * 100, 2)
        return s_returns

    @staticmethod
    def _number_of_trades(df):
        # Calculate number of trades
        df['new_order'] = df.position != df.position.shift(1).fillna(0)
        num_trades = df['new_order'].sum()
        return num_trades

    @staticmethod
    def _max_dd(df):
        # Calculate cumulative log returns
        df['cum_s_log_ret'] = df['s_log_ret'].cumsum()

        # Calculate the maximum cumulative log returns
        df['max_cum_s_log_ret'] = df['cum_s_log_ret'].cummax()

        # Drawdown is the difference between max cumulative log returns and current log returns
        df['drawdown'] = (df['cum_s_log_ret'] - df['max_cum_s_log_ret'])

        # Get the maximum drawdown
        dd = {'max_dd_period': str(pd.to_datetime(df.loc[df['drawdown'] == df['drawdown'].min()].index[0])),
              'max_dd_value': round((np.exp(df['drawdown'].min()) - 1) * 100, 2)}
        return dd

    def _pnl(self, df):
        df['cum_s_log_ret'] = df['s_log_ret'].cumsum()
        df['pnl'] = (self.initial_capital * df['cum_s_log_ret'].apply(np.exp) - self.initial_capital).round(2)
        return df.pnl

    def _buy_and_hold(self, df):
        # Calculate return of buy and hold strategy
        df['log_ret'] = (np.log(df['close'] / df['close'].shift(1))).fillna(0)
        df['cum_log_ret'] = df['log_ret'].cumsum()
        bnh_perc = round((np.exp(df['cum_log_ret'].iloc[-1] + np.log(1 - self.taker_fee)) - 1) * 100, 2)
        return bnh_perc

    def _sharpe_ratio(self, df):
        # Calculate annualized sharpe ratio
        df['s_ret'] = df.s_log_ret.apply(np.exp) - 1
        sharpe_ratio = round(df['s_ret'].mean() / df['s_ret'].std() * math.sqrt(self.YEARLY_TRADING_DAYS), 2)
        return sharpe_ratio

    def _win_rate(self, df):
        # Calculate the number of winning trades
        df['new_order'] = df.position != df.position.shift(1).fillna(0)
        df['trade'] = df.new_order.cumsum()
        df_agg = df.groupby('trade')['s_log_ret'].sum().reset_index()
        num_winning_trades = (df_agg['s_log_ret'] > 0).sum()

        # Calculate the total number of trades
        total_trades = len(df_agg)

        # Calculate the win rate
        win_rate = num_winning_trades / total_trades

        return win_rate

    def _calmar_ratio(self, df):
        # TODO
        pass

    def _gain_to_pain_ratio(self, df):
        # TODO
        pass

    def _profit_ratio(self, df):
        # TODO
        pass

    def get_metrics(self, df):
        metrics = {}
        try:
            df['s_log_ret'] = self._strategy_log_returns(df)
            metrics['rate_of_return'] = self._strategy_rate_of_return(df)
            metrics['profit_and_loss'] = self._pnl(df)
            metrics['buy_and_hold'] = self._buy_and_hold(df)
            metrics['max_drawdown'] = self._max_dd()
            metrics['sharpe_ratio'] = self._sharpe_ratio(df)
            metrics['number_of_trades'] = self._number_of_trades(df)
            metrics['wind_rate'] = self._win_rate(df)
            # metrics['calmar_ratio'] = self._calmar_ratio(df)
            # metrics['gain_to_pain_ratio'] = self._gain_to_pain_ratio(df)
            # metrics['profit_ratio'] = self._profit_ratio(df)

        except Exception as e:
            self.logger.error(f'Error computing the metrics: {e}')

        return metrics

    def compute_score(self, df):
        """
        Compute a combined score based on several metrics
        :return:
        """
        return self._strategy_rate_of_return(df)

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

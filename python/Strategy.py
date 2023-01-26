# -- Created by carlesferreres at 5/12/22

# -- Built-in and installed packages
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
# -- User custom function, classes and objects
from python.Indicators import Indicators
from python.PerformanceMetrics import PerformanceMetrics
from python.Logger import Logger


class Strategy(Indicators, PerformanceMetrics):

    def __init__(self, initial_capital, taker_fee):
        # Initialize parent classes
        Indicators.__init__(self)
        PerformanceMetrics.__init__(self, initial_capital, taker_fee)

        # Parameters
        self.data = pd.DataFrame
        self.results = pd.DataFrame
        self.results_all = pd.DataFrame()

        # Logger
        self.logger = Logger('Strat').get_logger()

    def run_macd(self, params):
        try:
            # Set parameters
            confirmation_perc = 0.02
            sma_short = params.get('sma_short')
            sma_long = params.get('sma_long')
            sma_short_name = f'SMA_{sma_short}'
            sma_long_name = f'SMA_{sma_long}'
            columns = ['close']

            # Compute indicators
            self.results = self.data[columns].copy()
            if sma_short < sma_long:
                self.sma(sma_short)
                self.sma(sma_long)

                # Set position based on indicators
                conditions = self.results[sma_short_name] > (self.results[sma_long_name] * (1+confirmation_perc))
                self.results['position'] = np.where(conditions, 1, 0)
            else:
                self.results['position'] = 0
        except Exception as e:
            self.logger.error(f'Error running the strategy: {e}')

    def run_modified_macd(self, params):
        try:
            # Set parameters
            confirmation_perc = 0.02
            sma_short = int(params.get('sma_short'))
            sma_long = int(params.get('sma_long'))
            sma_short_name = f'SMA_{sma_short}'
            sma_long_name = f'SMA_{sma_long}'
            columns = ['close']

            # Compute indicators
            self.results = self.data[columns].copy()
            if sma_short < sma_long:
                self.sma(sma_short)
                self.sma(sma_long)

                # Set position based on indicators
                conditions = ((self.results.close > self.results[sma_long_name] * (1+confirmation_perc)) &
                              (self.results[sma_short_name] > self.results[sma_long_name] * (1+confirmation_perc)),
                              (self.results.close > self.results[sma_long_name] * (1+confirmation_perc)) &
                              (self.results.close > self.results[sma_short_name] * (1+confirmation_perc)))
                choices = (1, 1)
                self.results['position'] = np.select(conditions, choices, 0)
            else:
                self.results['position'] = 0
        except Exception as e:
            self.logger.error(f'Error running the strategy: {e}')

    def run_bnh(self, params):
        columns = ['close']

        # Compute indicators
        self.results = self.data[columns].copy()
        self.results['position'] = 1

    def run_momentum_h(self, params):
        try:
            # Set parameters
            hurst_length = params.get('hurst_length')
            hurst_threshold = params.get('hurst_threshold')
            hurst_name = f'hurst_{hurst_length}'
            mom_name = f'mom_{hurst_length}'
            columns = ['close']

            # Compute indicators
            self.results = self.data[columns].copy()

            self.hurst(hurst_length)
            self.mom(hurst_length)

            # Set position based on indicators
            conditions = (self.results[hurst_name] > hurst_threshold) & (self.results[mom_name] > 0)
            self.results['position'] = np.where(conditions, 1, 0)
        except Exception as e:
            self.logger.error(f'Error running the strategy: {e}')

    def get_last_position(self):
        if not isinstance(self.results, pd.DataFrame):
            self.run_strategy()
        position_map = {-1: 'SHORT',
                        0: 'HOLD CASH',
                        1: 'LONG'}
        return position_map[self.results['position'].iloc[-1]]

    def set_data(self, data: pd.DataFrame):
        self.data = data

    def plot_data(self, words):
        """
        :param cols:
        :return:
        """
        columns = ['close']
        for word in words:
            columns = columns + [col for col in self.results.columns if word in col.lower()]
        plot_df = self.results.dropna().copy()
        plot_df['position'] = plot_df.position*70000
        fig = px.line(plot_df, x=plot_df.index, y=columns+['position'], color_discrete_map={'close': 'grey'})
        fig.show()



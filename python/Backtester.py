# -- Created by carlesferreres at 5/12/22 

# -- Built-in and installed packages
import datetime
import pandas as pd
import numpy as np
import math
from pprint import pprint
import plotly.express as px
import itertools as it
from sklearn.model_selection import TimeSeriesSplit
# -- User custom function, classes and objects
from python.Logger import Logger
from python.DatabaseWrapper import DatabaseWrapper
from python.ExchangeConnector import ExchangeConnector
from python.Strategy import Strategy


class Backtester:

    def __init__(self, pair: str = 'BTCUSDT', interval: str = '4h', initial_capital: int = 10000,
                 start_date: datetime = None, end_date: datetime = None):
        # Parameters
        self.start_date = start_date
        self.end_date = end_date
        self.pair = pair
        self.interval = interval
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.maker_fee = 0.1 / 100
        self.taker_fee = 0.1 / 100
        self.data = pd.DataFrame

        # Internal variables
        self._exchange_connector = ExchangeConnector()
        self._dbwrapper = DatabaseWrapper(self._exchange_connector)
        self._strategy = {}

        # Logger
        self.logger = Logger('BT').get_logger()

        # Initialise data and strategy
        self.get_data()
        self._strategy = Strategy(self.get_strategy_allocation(), self.taker_fee)

    def get_data(self):
        """
        Updates the data in the database for the pair and interval defined in the class.
        Then reads the data and does the requires transformations.
        :return:
        """
        # Update data
        try:
            self._dbwrapper.market_data_update(self.pair, self.interval)
        except Exception as e:
            self.logger.error(f'Data could not be updated: {e}')

        # Create query
        query = f"SELECT * FROM {self._dbwrapper.candles_table} WHERE pair='{self.pair}' AND interval='{self.interval}'"
        if self.start_date:
            query += f" AND open_time >= '{self.start_date}'"
        if self.end_date:
            query += f" AND close_time <= '{self.end_date}'"

        try:
            # Read and convert data
            self.data = self._dbwrapper.read_sql_table(query)
            self.data[['open_time', 'close_time']] = self.data[['open_time', 'close_time']].apply(pd.to_datetime)
            self.data.set_index('open_time', inplace=True)

            # Log data read
            self.logger.info(f'Successfully downloaded {str(len(self.data))} rows of data')
            self.logger.info(f'Data range from {self.data.index.min()} to {self.data.index.max()}')
        except Exception as e:
            self.logger.error(f'Error reading data from the db: {e}')

    def get_strategy_allocation(self):
        """
        Returns the initial capital for the strategy
        :return:
        """
        return self.initial_capital

    def get_taker_fee(self):
        """
        Gets the taker fee for the exchange defined
        :return:
        """
        # In the future, read from the from exchange
        return self.taker_fee

    def run_wfa(self, strategy: str, start_date: datetime = None, end_date: datetime = None):
        """
        Runs Walk Forward Analysis by selecting the best parameters that fit the trining set and testing the same values
        on the test set
        :param strategy:
        :param start_date:
        :param end_date:
        :return:
        """
        # Set parameters
        look_back = 500
        train_perc = 0.8
        param_grid = self.create_parameter_grid(strategy)
        train_size = math.ceil(look_back * train_perc)
        test_size = math.floor(look_back * round(1 - train_perc, 1))

        # Instantiate strategy
        self._strategy = Strategy(self.get_strategy_allocation(), self.taker_fee)
        self._strategy.wfa_scores = pd.DataFrame()

        # Filter data
        if not start_date and not end_date:
            data = self.data.copy()
        elif not start_date:
            data = self.data[self.data.index <= end_date]
        elif not end_date:
            data = self.data[self.data.index >= start_date]
        else:
            data = self.data[(self.data.index >= start_date) & (self.data.index <= end_date)]

        # Create splitter
        splits = (len(data) - train_size) // test_size
        tscv = TimeSeriesSplit(n_splits=splits, max_train_size=train_size, test_size=test_size)

        # Sliding window
        self.logger.info(f'Performing WFA on {len(data)} rows')
        for train_index, test_index in tscv.split(data):
            # Divide train and test sets
            train_data, test_data = data.iloc[train_index], data.iloc[test_index]

            # Save dates and set data
            first_train_date = train_data.index.min()
            first_test_date = test_data.index.min()
            last_date = test_data.index.max()

            # Add 100 more rows to train data
            train_data_long = data[data.index < first_test_date].copy()
            if len(train_data_long) > (len(train_data) + 100):
                train_data_long = train_data_long.iloc[-len(train_data) - 100:]
            train_data = train_data_long
            self._strategy.set_data(train_data)

            # Get best parameter combination
            self.logger.info(f'Optimising window from {first_train_date} to {last_date}')
            best_score = -np.inf
            for params in param_grid:
                # Run strategy
                score = self.run_backtest(strategy=strategy, params=params, data=train_data,
                                          first_date=first_train_date)
                # Keep best score
                if score > best_score:
                    best_score = score
                    opt_params = params
                    self.logger.info(f'    New best score: {best_score}. '
                                     f'    Parameters: {params}')

            # Add 100 more rows to test data
            test_data_long = data[data.index <= last_date].copy()
            if len(test_data_long) > (len(test_data) + 100):
                test_data_long = test_data_long.iloc[-len(test_data) - 100:]
            test_data = test_data_long

            # Get test score and save train and test scores into wfa_scores
            test_score = self.run_backtest(strategy=strategy, params=opt_params, data=test_data,
                                           first_date=first_test_date, append_results=True)
            new_row = {'train_score': [best_score], 'test_score': [test_score], 'parameters': [opt_params],
                       'first_train_date': [first_train_date], 'first_test_date': [first_test_date],
                       'last_test_date': [last_date]}
            self._strategy.wfa_scores = pd.concat([self._strategy.wfa_scores, pd.DataFrame(new_row)], ignore_index=True)

        self.get_wfa_output(strategy)

    def run_backtest(self, strategy: str, params: dict, data: pd.DataFrame = None, first_date: datetime = None,
                     append_results: bool = False):
        """
        Runs and calculates the score for a given strategy and set of parameters
        :param strategy: strategy name corresponding to a function in Strategy class
        :param params: set of parameters used to run the strategy
        :param data: dataframe containing the data the use for the strategy
        :param first_date: first date used to calculate the score, used in WFA so that we can run the strategy with
        past data and calculate the required indicators.
        :param append_results: True if results need to be appended to results_all dataframe
        :return: numerical value representing the score
        """
        # Set data
        if data is None:
            data = self.data
        self._strategy.set_data(data)

        # Run strategy
        getattr(self._strategy, 'run_' + strategy)(params)

        # Excludes extra rows added for calculation purposes
        if first_date:
            self._strategy.results = self._strategy.results[self._strategy.results.index >= first_date]

        # Append results to result_all when we have test results
        if append_results:
            self._strategy.results_all = pd.concat([self._strategy.results_all,
                                                    self._strategy.results[['close', 'position']]])
        return self._strategy.get_score(self._strategy.results)

    def create_parameter_grid(self, strategy: str):
        """
        Creates a grid of all parameter combinations given the start, end, and step value for each parameter
        :param strategy: name of the backtesting strategy
        :return: dictionary of all combinations
        """
        # Read data from database
        query = f"SELECT * FROM {self._dbwrapper.parameters_table} WHERE strategy = '{strategy}'"
        params_df = self._dbwrapper.read_sql_table(query)

        # Create grid
        params_dict = dict()
        params_df.loc[params_df.step == 0, 'step'] = 1
        for i, row in params_df.iterrows():
            params_dict[row['parameter']] = list(np.arange(row['start_value'], row['end_value'] + row['step'],
                                                           row['step']). round(3))
        values = [*it.product(*params_dict.values())]
        params_grid = [dict([*zip(params_dict.keys(), val)]) for val in values]

        return params_grid

    def get_wfa_output(self, strategy):
        """
        Computes all the metrics for the whole range of backtested history
        :param strategy: name of the backtested strategy
        :return:
        """
        # Compute metrics
        print(f'Strategy: {strategy} \n'
              f'Pair: {self.pair} \n'
              f'Timeframe: {self.interval} \n'
              f'Test results range: \n'
              f'    From: {self._strategy.results_all.index.min()} \n'
              f'    To: {self._strategy.results_all.index.max()} \n'
              f'Performance Metrics: ')
        pprint(self._strategy.get_metrics(self._strategy.results_all), sort_dicts=False, width=60)

        print(f'Train(pnl): {round(self._strategy.wfa_scores.train_score.mean(), 2)} \n'
              f'Test(pnl): {round(self._strategy.wfa_scores.test_score.mean(), 2)}')
        # Plot
        # self._strategy.plot_results()
        print("Last recommendation: " + self._strategy.get_last_position())

    def plot_data(self):
        """
        :param cols: 
        :return: 
        """
        fig = px.line(self.data, x='open_time', y='close', title=self.pair, color='black')
        fig.show()


if __name__ == '__main__':
    bt_parameters = {'pair': 'BTCUSDT',
                     'interval': '1d',
                     'strategy': 'bnh'}
    bt = Backtester(interval=bt_parameters.get('interval'), pair=bt_parameters.get('pair')) # , start_date=pd.to_datetime('20210101'))
    bt.run_wfa(strategy=bt_parameters.get('strategy'))
    print('a')


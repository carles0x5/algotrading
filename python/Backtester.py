# -- Created by carlesferreres at 5/12/22 

# -- Built-in and installed packages
import datetime
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
# -- User custom function, classes and objects
from python.Logger import Logger
from python.DatabaseWrapper import DatabaseWrapper
from python.Strategy import Strategy


class Backtester:

    def __init__(self, pair: str = 'BTCUSDT', interval: str = '1d', initial_capital: int = 10000, 
                 start_date: datetime = None, end_date: datetime = None):
        self.start_date = start_date
        self.end_date = end_date
        self.pair = pair
        self.interval = interval
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.maker_fee = 0.5 / 100
        self.taker_fee = 0.5 / 100
        self.metrics = {}
        self.strategy = Strategy()
        self.data = pd.DataFrame

        # Internal variables
        self._dbwrapper = DatabaseWrapper() 

        # Logger
        self.logger = Logger('BT').logger
        pass

    def get_data(self):
        # Create query
        query = f"SELECT * FROM {self._dbwrapper.candles_table} WHERE pair='{self.pair}' AND interval='{self.interval}'"
        if self.start_date:
            query += f" AND open_time >= '{self.start_date}'"
        if self.end_date:
            query += f" AND close_time <= '{self.end_date}'"

        # Read and convert data
        self.data = self._dbwrapper.read_sql_table(query)
        self.data[['open_time', 'close_time']] = self.data[['open_time', 'close_time']].apply(pd.to_datetime)

        # Log data read
        self.logger.info(f'Successfully downloaded {str(len(self.data))} rows of data')

    def run_backtest(self):
        # Get data
        self._dbwrapper.market_data_update(self.pair, self.interval)
        self.get_data()

        # Run strategy
        self.strategy.set_data(self.data)
        self.strategy.run_strategy()

        # Compute metrics

        pass

    def plot_data(self):
        """
        :param cols: 
        :return: 
        """
        # self.data[cols].plot(figsize=(10, 6), title=self.pair)
        sns.lineplot(self.data, x='open_time', y='close').set(title=self.pair)
        plt.show()


if __name__ == '__main__':
    bt = Backtester()
    bt.run_backtest()

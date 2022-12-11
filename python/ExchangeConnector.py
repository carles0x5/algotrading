# Created by carlesferreres at 28/11/22

# Built-in and installed packages
import pandas as pd
import time
# User custom function, classes and objects
from python.AppConfig import AppConfig
from binance.spot import Spot
from python.Logger import Logger


class ExchangeConnector(AppConfig):
    """
    Exchange connector for Spot trading
    """
    def __init__(self, exchange: str = 'Binance'):
        super().__init__()
        if exchange.upper() == 'BINANCE':
            self.client = Spot(key=self._api_key, secret=self._api_secret)
        self.logger = Logger('EC').logger

    def read_candlestick_data(self, pair: str, interval: str = '1d', start_ts: int = None, end_ts: int = None,
                              limit: int = 1000) -> pd.DataFrame:
        """
        :param pair: Currency pair for data request
        :param interval: data granularity as string (e.g. '1h', '4h', '1d', '1w')
        :param start_ts: starting timestamp of data request in miliseconds
        :param end_ts: ending timestamp of data request in miliseconds
        :param limit: Maximum number of rows to return
        :return: pandas dataframe with candelstick data
        """

        # Read candles using client connection
        params = {'symbol': pair,
                  'interval': interval,
                  'startTime': start_ts,
                  'endTime': end_ts,
                  'limit': limit}
        data = self._method('klines', params)
            
        data = pd.DataFrame(data, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                                           'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                                           'taker_buy_quote_asset_volume', 'ignore'], dtype=float)

        # Filter, add, and convert data
        columns_filter = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'number_of_trades']
        data = data[columns_filter]
        data.insert(0, 'interval', interval)
        data.insert(0, 'pair', pair)
        data[['open_time', 'close_time']] = data[['open_time', 'close_time']].apply(pd.to_datetime, unit='ms')
        return data

    def _method(self, endpoint: str, params: dict = None):
        try:
            method = getattr(self.client, endpoint)
            return method() if params is None else method(**params)
        except Exception as e:
            self.logger.error(f'Error calling {endpoint}: {e}')


if __name__ == '__main__':
    connector = ExchangeConnector()
    candles = connector.read_candlestick_data(pair='BTCUSDT', interval='1d')
    print(candles.iloc[0]['open_time'])

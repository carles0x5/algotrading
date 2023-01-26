# Created by carlesferreres at 28/11/22

# Built-in and installed packages
import sqlite3
import os
import calendar
import time
from pathlib import Path
import math
import pandas as pd
from sqlalchemy import create_engine
from dateutil import relativedelta
import datetime
from dateutil import tz
# User custom function, classes and objects
from python.ExchangeConnector import ExchangeConnector
from python.Logger import Logger


class DatabaseWrapper:
    MIN_RECORDS = 10000
    MAX_RECORDS = 20000
    SEC_PER_MIN = 60
    MIN_PER_H = 60
    H_PER_DAY = 24
    DAY_PER_W = 7
    DEFAULT_API_LIMIT = 1000
    BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parents[0]

    def __init__(self, exchange_connector=None):
        self.database_name = 'db/db'
        self.candles_table = 'RAW_CANDLES_DATA'
        self.parameters_table = 'OPTIMISATION_PARAMETERS'

        # Internal variables
        self._exchange_connector = exchange_connector if exchange_connector else ExchangeConnector()
        self._sql_connection = {}

        # Logger
        self.logger = Logger('DBW').logger

        # Functions
        self.create_connection()

    def create_connection(self):
        try:
            db_path = os.path.join(self.BASE_DIR, "{}.db".format(self.database_name))
            self._sql_connection = create_engine('sqlite:///' + db_path, echo=False)
        except Exception as e:
            self.logger.error(f'Error creating SQL connection: {e}')

    def execute_sql_procedure(self, query: str):
        try:
            return self._sql_connection.execute(query)
        except Exception as e:
            self.logger.error(f'Error executing SQL procedure: {e}')

    def read_sql_table(self, query: str):
        try:
            return pd.read_sql(query, con=self._sql_connection)
        except Exception as e:
            self.logger.error(f'Error reading SQL table: {e}')

    def market_data_update(self, pair: str, interval: str):
        # Set initial values
        amount = int(interval[0])
        unit = interval[1]
        current_ts_s = time.time()

        # Delete rows before first date to comply with MAX_RECORDS
        max_sec_diff = self.MAX_RECORDS * \
                       (self.DAY_PER_W * self.H_PER_DAY * self.MIN_PER_H * self.SEC_PER_MIN * int(unit == 'w') +
                        self.H_PER_DAY * self.MIN_PER_H * self.SEC_PER_MIN * int(unit == 'd') +
                        self.MIN_PER_H * self.SEC_PER_MIN * int(unit == 'h') +
                        self.SEC_PER_MIN * int(unit == 'm')) * amount
        first_ts_s = max(current_ts_s - max_sec_diff, 0)
        first_date = pd.to_datetime(first_ts_s * 1e9)
        query = f"DELETE FROM {self.candles_table} WHERE pair = '{pair}' AND interval = '{interval}' " \
                f"AND open_time < '{first_date}'"
        self.execute_sql_procedure(query)

        # Delete last row to update last price
        query = f"DELETE FROM {self.candles_table} WHERE pair = '{pair}' AND interval = '{interval}' " \
                f"AND open_time = (SELECT MAX(open_time) as max_date FROM {self.candles_table} " \
                f"WHERE pair = '{pair}' AND interval = '{interval}')"
        self.execute_sql_procedure(query)

        # Select latest date for pair and interval in database
        query = f"SELECT MAX(open_time) as max_date FROM {self.candles_table} " \
                f"WHERE pair = '{pair}' AND interval = '{interval}'"
        res = self.read_sql_table(query)
        max_date = res['max_date'].values[0]

        # Get amount of records to insert and difference in seconds between present and first value to insert
        if max_date:
            max_date_ts_s = calendar.timegm(pd.to_datetime(max_date).timetuple())
            delta_s = current_ts_s - max_date_ts_s

        records = math.floor(delta_s /
                             (self.SEC_PER_MIN * self.MIN_PER_H * self.H_PER_DAY * self.DAY_PER_W * int(unit == 'w') +
                              self.SEC_PER_MIN * self.MIN_PER_H * self.H_PER_DAY * int(unit == 'd') +
                              self.SEC_PER_MIN * self.MIN_PER_H * int(unit == 'h') +
                              self.SEC_PER_MIN * int(unit == 'm'))
                             / amount) if max_date else self.MIN_RECORDS
        sec_diff = records * (self.DAY_PER_W * self.H_PER_DAY * self.MIN_PER_H * self.SEC_PER_MIN * int(unit == 'w') +
                              self.H_PER_DAY * self.MIN_PER_H * self.SEC_PER_MIN * int(unit == 'd') +
                              self.MIN_PER_H * self.SEC_PER_MIN * int(unit == 'h') +
                              self.SEC_PER_MIN * int(unit == 'm')) * amount
        from_ts_s = max(current_ts_s - sec_diff, 0)
        sec_diff = current_ts_s - from_ts_s

        # Write values to database by reading a maximum of 1000 records at a time
        iterations = math.ceil(records / self.DEFAULT_API_LIMIT)
        rows = 0
        for i in range(iterations):
            to_ts_s = from_ts_s + sec_diff // iterations
            data = self._exchange_connector.read_candlestick_data(pair=pair, interval=interval,
                                                                  start_ts=round(from_ts_s * 1e3),
                                                                  end_ts=round(to_ts_s * 1e3))
            rows += len(data)
            from_ts_s = to_ts_s
            res = data.to_sql(self.candles_table, con=self._sql_connection, if_exists='append', index=False)

        self.logger.info(f'Rows inserted in {self.candles_table} : {str(rows)}')
        return 0

    def get_exchange_connector(self):
        return self._exchange_connector

    def get_sql_connector(self):
        return self._sql_connection


if __name__ == '__main__':
    dbw = DatabaseWrapper()
    # query = f"DELETE FROM {dbw.candles_table}"
    # dbw.execute_sql_procedure(query)
    dbw.market_data_update(pair='BTCUSDT', interval='4h')

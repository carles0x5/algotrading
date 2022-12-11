import sqlite3
from pprint import pprint

from binance.spot import Spot
import config
import logging
import pandas as pd
import matplotlib.pyplot as plt

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                        datefmt='%Y/%m/%d %I:%M:%S %p',
                        level=logging.INFO)
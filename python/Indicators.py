# -- Created by carlesferreres at 11/12/22 

# -- Built-in and installed packages
import pandas as pd
import pyeeg
import numpy as np
# -- User custom function, classes and objects
from python.Logger import Logger


class Indicators:

    def __init__(self):
        # Parameters
        self.results = pd.DataFrame

        # Logger
        self.logger = Logger('Ind').get_logger()

    def sma(self, length: int):
        name = f'SMA_{length}'
        self.results[name] = self.results['close'].rolling(window=length).mean()

    def ema(self, length: int):
        name = f'EMA_{length}'
        self.results[name] = self.results['close'].ewm(span=length, adjust=False).mean()

    def hurst(self, length: int):
        name = f'hurst_{length}'
        self.results[name] = self.results['close'].rolling(length).apply(lambda x: pyeeg.hurst(x))

    def mom(self, length):
        name = f'mom_{length}'
        self.results[name] = self.results['close'].pct_change(periods=length)

    def rsi(self):
        pass

    def adr(self):
        pass

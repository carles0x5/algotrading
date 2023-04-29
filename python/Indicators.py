# -- Created by carlesferreres at 11/12/22 

# -- Built-in and installed packages
import pandas as pd
import pyeeg
import numpy as np
# -- User custom function, classes and objects
from python.Logger import Logger


class Indicators:

    def __init__(self):
        # Logger
        self.logger = Logger(self.__class__.__name__).logger

    @staticmethod
    def sma(df, length: int, column='close'):
        sma_vals = df[column].rolling(window=length).mean()
        return sma_vals

    @staticmethod
    def ema(df, length: int, column='close'):
        ema_vals = df[column].ewm(span=length, adjust=False).mean()
        return ema_vals

    @staticmethod
    def hurst(df, length: int, column='close'):
        hurst_vals = df[column].rolling(length).apply(lambda x: pyeeg.hurst(x))
        return hurst_vals

    @staticmethod
    def mom(df, length, column='close'):
        mom_vals = df[column].pct_change(periods=length)
        return mom_vals

    def rsi(self):
        pass

    def adr(self):
        pass

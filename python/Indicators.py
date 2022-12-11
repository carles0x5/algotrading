# -- Created by carlesferreres at 11/12/22 

# -- Built-in and installed packages
import pandas as pd
# -- User custom function, classes and objects


class Indicators:

    def __init__(self):
        self.data = pd.DataFrame

    def sma(self, length: int):
        name = f'SMA_{str(length)}'
        self.data[name] = self.data['close'].rolling(window=length).mean()

    def ema(self, length: int):
        name = f'EMA_{str(length)}'
        self.data[name] = self.data['close'].ewm(span=20, adjust=False).mean()
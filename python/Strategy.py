# -- Created by carlesferreres at 5/12/22

# -- Built-in and installed packages
import pandas as pd
# -- User custom function, classes and objects
from python.Indicators import Indicators


class Strategy(Indicators):

    def __init__(self):
        self.data = pd.DataFrame
        self.results = pd.DataFrame

    def run_strategy(self):
        self.sma(50)
        return 0

    def set_data(self, data):
        self.data = data


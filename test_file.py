# -- Created by carlesferreres at 6/1/23 

# -- Built-in and installed packages
import ccxt
import config
# -- User custom function, classes and objects

exchange = ccxt.binance({
        'apiKey': config.API_KEY,
        'secret': config.API_SECRET_KEY
    })


# Created by carlesferreres at 28/11/22

# Built-in and installed packages
# User custom function, objects, and files
import config


class AppConfig:
    def __init__(self):
        self._api_key = config.API_KEY
        self._api_secret = config.API_SECRET_KEY



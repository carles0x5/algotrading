# Created by carlesferreres at 3/12/22 

# Built-in and installed packages
import logging
# User custom function, classes and objects


class Logger:

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.set_config()

    @staticmethod
    def set_config():
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                            datefmt='%Y/%m/%d %I:%M:%S %p',
                            level=logging.INFO)

    @property
    def logger(self):
        return self.logger

    @logger.setter
    def logger(self, name):
        self.logger = logging.getLogger(name)

if __name__ == '__main__':
    logger = Logger('TEST')
    logger.logger.info('test message')


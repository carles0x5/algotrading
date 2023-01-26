# Created by carlesferreres at 3/12/22 

# Built-in and installed packages
import logging
# User custom function, classes and objects


def set_config():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                        datefmt='%Y/%m/%d %I:%M:%S %p',
                        level=logging.INFO)


class Logger:

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        set_config()

    def get_logger(self):
        return self.logger


if __name__ == '__main__':
    logger = Logger('TEST')
    logger.logger.info('test message')


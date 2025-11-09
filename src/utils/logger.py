import json
import logging.config
import logging.handlers
import pathlib


class testinglog:
    def __init__ (self):
        self.logger = logging.getLogger("my_app")

    def setup_logging(self):
        config_file = pathlib.Path(__file__).parent / "logging_configs" / "config.json"
        with open(config_file) as f_in:
            config = json.load(f_in)
        logging.config.dictConfig(config)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)
import json
import logging
import logging.config
import pathlib
import os
from typing import Optional


class AppLogger:
    """Centralized logger for the sentiment analyzer application"""
    _instance: Optional['AppLogger'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not AppLogger._initialized:
            self._setup_logging()
            self.logger = logging.getLogger("sentiment_analyzer")
            AppLogger._initialized = True

    def _setup_logging(self) -> None:
        """Load logging configuration from JSON file"""
        config_file = pathlib.Path(__file__).parent / "logging_configs" / "config.json"
        try:
            with open(config_file) as f_in:
                config = json.load(f_in)
                os.makedirs("logs", exist_ok=True)
            logging.config.dictConfig(config)
        except FileNotFoundError:
            logging.basicConfig(level=logging.INFO)
            logging.warning(f"Logging config file not found at {config_file}, using basic config")
        except json.JSONDecodeError as e:
            logging.basicConfig(level=logging.INFO)
            logging.error(f"Invalid JSON in logging config: {e}")

    def debug(self, msg: str, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(msg, extra=kwargs)

    def info(self, msg: str, **kwargs) -> None:
        """Log info message"""
        self.logger.info(msg, extra=kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(msg, extra=kwargs)

    def error(self, msg: str, **kwargs) -> None:
        """Log error message"""
        self.logger.error(msg, extra=kwargs)

    def critical(self, msg: str, **kwargs) -> None:
        """Log critical message"""
        self.logger.critical(msg, extra=kwargs)

    def exception(self, msg: str, **kwargs) -> None:
        """Log exception with traceback"""
        self.logger.exception(msg, extra=kwargs)


def get_logger() -> AppLogger:
    """Get the singleton logger instance"""
    return AppLogger()
"""
Logging Configuration for AI-Powered Requirements Engineering Tool
Provides structured logging with file and console handlers
"""

import logging
import logging.handlers
import os
from datetime import datetime
from config import AppConfig

class LoggerFactory:
    """Factory for creating configured loggers"""

    _loggers = {}

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get or create a logger with the specified name"""

        if name in LoggerFactory._loggers:
            return LoggerFactory._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(AppConfig.LOG_LEVEL)

        # Create formatters
        formatter = logging.Formatter(AppConfig.LOG_FORMAT)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(AppConfig.LOG_LEVEL)
        console_handler.setFormatter(formatter)

        # File handler with rotation
        log_file = os.path.join(
            AppConfig.LOGS_DIR,
            f"ai_re_tool_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(AppConfig.LOG_LEVEL)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        LoggerFactory._loggers[name] = logger
        return logger


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger"""
    return LoggerFactory.get_logger(name)

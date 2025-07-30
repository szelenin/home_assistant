import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional


class HomeAssistantLogger:
    """Centralized logging utility for Home Assistant with daily file rolling."""
    
    def __init__(self, name: str = "home_assistant", log_level: str = "INFO"):
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with console and file handlers."""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create logs directory if it doesn't exist
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
        
        # File handler with daily rotation (DEBUG and above)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=os.path.join(logs_dir, "home_assistant.log"),
            when="midnight",
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # Error file handler (ERROR and above)
        error_handler = logging.handlers.TimedRotatingFileHandler(
            filename=os.path.join(logs_dir, "home_assistant_error.log"),
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
        
        return logger
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message."""
        self.logger.critical(message)
    
    def exception(self, message: str):
        """Log exception with traceback."""
        self.logger.exception(message)


# Global logger instance
_logger: Optional[HomeAssistantLogger] = None


def get_logger(name: str = "home_assistant", log_level: str = "INFO") -> HomeAssistantLogger:
    """Get or create a logger instance."""
    global _logger
    if _logger is None:
        _logger = HomeAssistantLogger(name, log_level)
    return _logger


def setup_logging(name: str = "home_assistant", log_level: str = "INFO") -> HomeAssistantLogger:
    """Setup and return a logger instance."""
    return get_logger(name, log_level) 
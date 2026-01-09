"""
Logging system for SimpleNES-py
Implements a configurable logging system with support for console and file output
"""
import logging
import logging.handlers
import sys
from typing import Optional
from .config import Config


class LoggerManager:
    """Manages logging for the SimpleNES emulator"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config = Config()
        self.logger = None
        self._setup_logger()
        self._initialized = True
    
    def _setup_logger(self):
        """Set up the logger based on configuration"""
        log_config = self.config.get_logging_config()
        
        # Create logger
        self.logger = logging.getLogger('SimpleNES')
        self.logger.setLevel(self._get_log_level(log_config.get('level', 'INFO')))
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Set formatter
        log_format = log_config.get('format', '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
        formatter = logging.Formatter(log_format)
        
        # Add console handler if enabled
        if log_config.get('console_output', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Add file handler if enabled
        if log_config.get('file_output', True):
            file_path = log_config.get('file_path', 'simple_nes.log')
            try:
                file_handler = logging.FileHandler(file_path, encoding='utf-8')
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                print(f"Could not create log file {file_path}: {e}")
    
    def _get_log_level(self, level_str: str) -> int:
        """Convert string log level to logging constant"""
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return levels.get(level_str.upper(), logging.INFO)
    
    def get_logger(self):
        """Get the configured logger instance"""
        if not self.logger:
            self._setup_logger()
        return self.logger
    
    def reload_config(self):
        """Reload configuration and update logger"""
        self.config = Config()
        self._setup_logger()


# Convenience functions
def get_logger():
    """Get the SimpleNES logger instance"""
    return LoggerManager().get_logger()


def debug(message: str, *args, **kwargs):
    """Log a debug message"""
    get_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """Log an info message"""
    get_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """Log a warning message"""
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """Log an error message"""
    get_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """Log a critical message"""
    get_logger().critical(message, *args, **kwargs)


def init_logging():
    """Initialize the logging system"""
    LoggerManager()
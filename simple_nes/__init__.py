"""
SimpleNES - A Python implementation of an NES emulator

This package contains all the core modules for emulating the Nintendo Entertainment System.
"""

# SimpleNES package
from .util.config import Config
from .util.logging import LoggerManager, get_logger, debug, info, warning, error, critical, init_logging

__all__ = [
    'Config',
    'LoggerManager', 
    'get_logger',
    'debug',
    'info', 
    'warning',
    'error',
    'critical',
    'init_logging'
]
"""
Configuration management for SimpleNES-py
Handles logging configuration and controller settings
"""
import json
import os
from typing import Dict, Any, Optional

class Config:
    """Configuration class for SimpleNES-py"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration with optional config file path"""
        if config_path and os.path.exists(config_path):
            self.config_path = config_path
            self.config_data = self.load_config(config_path)
        else:
            # Use default config path or create default config
            self.config_path = config_path or "config.json"
            self.config_data = self.get_default_config()
            # Create config file if it doesn't exist
            if not os.path.exists(self.config_path):
                self.save_config(self.config_path, self.config_data)
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_path}, using default configuration")
            return self.get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error parsing config file {config_path}: {e}, using default configuration")
            return self.get_default_config()
    
    def save_config(self, config_path: str, config_data: Dict[str, Any]):
        """Save configuration to JSON file"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config file {config_path}: {e}")
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "logging": {
                "level": "INFO",
                "file_path": "simple_nes.log",
                "console_output": True,
                "file_output": True,
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
            },
            "controller": {
                "player1": {
                    "A": "K_j",           # A button
                    "B": "K_k",           # B button
                    "SELECT": "K_RSHIFT", # Select
                    "START": "K_RETURN",  # Start
                    "UP": "K_w",          # Up
                    "DOWN": "K_s",        # Down
                    "LEFT": "K_a",        # Left
                    "RIGHT": "K_d"        # Right
                },
                "player2": {
                    "A": "K_KP5",         # A button
                    "B": "K_KP6",         # B button
                    "SELECT": "K_KP8",    # Select
                    "START": "K_KP9",     # Start
                    "UP": "K_UP",         # Up
                    "DOWN": "K_DOWN",     # Down
                    "LEFT": "K_LEFT",     # Left
                    "RIGHT": "K_RIGHT"    # Right
                }
            }
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config_data.get("logging", self.get_default_config()["logging"])
    
    def get_controller_config(self) -> Dict[str, Any]:
        """Get controller configuration"""
        return self.config_data.get("controller", self.get_default_config()["controller"])
    
    def update_config(self, section: str, key: str, value: Any):
        """Update a specific configuration value"""
        if section not in self.config_data:
            self.config_data[section] = {}
        self.config_data[section][key] = value
        
    def save_current_config(self):
        """Save the current configuration to file"""
        self.save_config(self.config_path, self.config_data)
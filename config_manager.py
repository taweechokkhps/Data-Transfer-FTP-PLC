"""
Compatibility shim for config_manager.py - redirects imports to core.config_service.
"""
from core.config_service import ConfigManager, DEFAULT_CONFIG, CONFIG_FILE

__all__ = ["ConfigManager", "DEFAULT_CONFIG", "CONFIG_FILE"]

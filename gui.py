"""
Compatibility shim for gui.py - redirects imports to the modular ui package.
"""
from ui.app import App
from ui.components.tooltip import ToolTip
from ui.components.log_console import LogConsole

__all__ = ["App", "ToolTip", "LogConsole"]

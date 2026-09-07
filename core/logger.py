import time
import os
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

class AppLogger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
            cls._instance._init_logger()
        return cls._instance

    def _init_logger(self):
        self.callbacks = []
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"

        self.file_logger = logging.getLogger("FTPControlApp")
        self.file_logger.setLevel(logging.INFO)
        if not self.file_logger.handlers:
            handler = RotatingFileHandler(str(log_file), maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            self.file_logger.addHandler(handler)

    def register_callback(self, callback):
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def unregister_callback(self, callback):
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def log(self, message: str, level: str = "info"):
        timestamp = time.strftime("%H:%M:%S")
        formatted_ui = f"[{timestamp}] {message}"
        
        lower = level.lower() if level else "info"
        if lower == "error":
            self.file_logger.error(message)
        elif lower == "warning":
            self.file_logger.warning(message)
        else:
            self.file_logger.info(message)

        for cb in list(self.callbacks):
            try:
                cb(formatted_ui, level)
            except Exception:
                pass

    def info(self, message: str): self.log(message, "info")
    def success(self, message: str): self.log(message, "success")
    def warning(self, message: str): self.log(message, "warning")
    def error(self, message: str): self.log(message, "error")

logger = AppLogger()

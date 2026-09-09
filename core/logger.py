import time
import datetime
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
            formatter = logging.Formatter("[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            self.file_logger.addHandler(handler)

    def register_callback(self, callback):
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def unregister_callback(self, callback):
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def log(self, message: str, level: str = "info"):
        raw_level = (level or "").lower().strip()
        lower_msg = message.lower()

        # Smart fallback if level is generic 'info' or None
        if not raw_level or raw_level == "info":
            if "❌" in message or "error" in lower_msg or "failed" in lower_msg:
                raw_level = "error"
            elif "502" in lower_msg or "switching to active" in lower_msg:
                raw_level = "switch_mode"
            elif "download process completed" in lower_msg and "✅" in message:
                raw_level = "completed"
            elif "downloaded" in lower_msg or "converted to csv" in lower_msg or "download process completed" in lower_msg:
                raw_level = "success"
            elif "warning" in lower_msg or "skipped" in lower_msg:
                raw_level = "warning"
            else:
                raw_level = "info"

        # Canonical tag and level normalization
        if raw_level in ["switch_mode", "switch mode", "switch"]:
            canonical_tag = "SWITCH MODE"
            norm_level = "switch_mode"
        elif raw_level in ["completed"]:
            canonical_tag = "SUCCESS"
            norm_level = "completed"
        elif raw_level in ["success", "ok"]:
            canonical_tag = "SUCCESS"
            norm_level = "success"
        elif raw_level in ["error", "fail", "failed"]:
            canonical_tag = "ERROR"
            norm_level = "error"
        elif raw_level in ["warning", "warn"]:
            canonical_tag = "WARNING"
            norm_level = "warning"
        else:
            canonical_tag = "INFO"
            norm_level = "info"

        now = datetime.datetime.now()
        timestamp = now.strftime("%H:%M:%S.%f")[:-3]

        # Avoid duplicating tag if message already starts with [TAG]
        clean_msg = message
        tag_prefix = f"[{canonical_tag}]"
        if clean_msg.startswith(tag_prefix):
            clean_msg = clean_msg[len(tag_prefix):].strip()

        formatted_ui = f"[{timestamp}] [{canonical_tag}] {clean_msg}"

        if norm_level == "error":
            self.file_logger.error(f"[{canonical_tag}] {clean_msg}")
        elif norm_level == "warning":
            self.file_logger.warning(f"[{canonical_tag}] {clean_msg}")
        else:
            self.file_logger.info(f"[{canonical_tag}] {clean_msg}")

        for cb in list(self.callbacks):
            try:
                cb(formatted_ui, norm_level)
            except Exception:
                pass

    def info(self, message: str): self.log(message, "info")
    def success(self, message: str): self.log(message, "success")
    def completed(self, message: str): self.log(message, "completed")
    def warning(self, message: str): self.log(message, "warning")
    def error(self, message: str): self.log(message, "error")
    def switch_mode(self, message: str): self.log(message, "switch_mode")

logger = AppLogger()

from tkinter import filedialog
from typing import Optional, Dict, Any, Tuple, List
from core.logger import logger

class SettingsController:
    """Controller handling business logic and persistence for application settings."""

    DEFAULT_EXTENSIONS = [".txt", ".csv"]
    DEFAULT_INTERVAL = 60

    def __init__(self, config_manager, app_logger=None):
        self.config_manager = config_manager
        self.logger = app_logger or logger

    def get_settings(self) -> Dict[str, Any]:
        """Retrieve current global settings."""
        return self.config_manager.get().get("global_settings", {})

    @staticmethod
    def format_extension(ext: str) -> Optional[str]:
        """Normalize file extension string (e.g. 'LOG' -> '.log')."""
        if not ext:
            return None
        cleaned = ext.strip().lower()
        if not cleaned:
            return None
        if not cleaned.startswith("."):
            cleaned = "." + cleaned
        return cleaned

    def browse_target_dir(self, initial_dir: str = "") -> Optional[str]:
        """Open directory picker dialog and return selected path if any."""
        chosen = filedialog.askdirectory(title="Select Target Save Directory", initialdir=initial_dir)
        if chosen:
            return chosen.replace("\\", "/")
        return None

    def save_settings(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate and save global settings into config_manager.
        Returns (success: bool, message: str).
        """
        try:
            target_dir = str(data.get("target_directory", "")).strip()

            # Process file extensions
            raw_exts = data.get("file_extensions", [])
            cleaned_exts = []
            for ext in raw_exts:
                norm = self.format_extension(ext)
                if norm and norm not in cleaned_exts:
                    cleaned_exts.append(norm)

            if not cleaned_exts:
                cleaned_exts = list(self.DEFAULT_EXTENSIONS)

            # Process interval
            raw_interval = data.get("auto_pull_interval_minutes", self.DEFAULT_INTERVAL)
            try:
                interval = int(raw_interval)
                if interval <= 0:
                    interval = self.DEFAULT_INTERVAL
            except (ValueError, TypeError):
                interval = self.DEFAULT_INTERVAL

            # Process boolean flags
            auto_pull_enabled = bool(data.get("auto_pull_enabled", True))
            separate_by_date = bool(data.get("separate_by_date", False))

            # Process lines
            auto_pull_lines = data.get("auto_pull_lines", [])
            if not isinstance(auto_pull_lines, list):
                auto_pull_lines = []

            settings = {
                "target_directory": target_dir,
                "file_extensions": cleaned_exts,
                "separate_by_date": separate_by_date,
                "auto_pull_enabled": auto_pull_enabled,
                "auto_pull_interval_minutes": interval,
                "auto_pull_lines": auto_pull_lines
            }

            self.config_manager.update_global_settings(settings)
            self.logger.info("Settings saved successfully.")
            return True, "Settings saved successfully"
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            return False, f"Failed to save settings: {e}"

import json
import os
from pathlib import Path

CONFIG_FILE = "config.json"

DEFAULT_TARGET_DIR = str(Path.home() / "Desktop" / "PLC_Downloads").replace("\\", "/")

DEFAULT_CONFIG = {
    "global_settings": {
        "target_directory": DEFAULT_TARGET_DIR,
        "file_extensions": [".txt", ".csv"],
        "separate_by_date": False,
        "auto_pull_interval_minutes": 60
    },
    "plcs": []
}

class ConfigManager:
    def __init__(self, config_path=CONFIG_FILE):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                needs_save = False
                for plc in data.get("plcs", []):
                    if "group" in plc:
                        del plc["group"]
                        needs_save = True
                    
                    # Migrate old comma-separated remote_directory to machines list
                    if "machines" not in plc:
                        r_dirs_raw = plc.get("remote_directory", "")
                        dirs = [d.strip() for d in r_dirs_raw.split(",") if d.strip()]
                        default_names = ["MC1 Connector Leak", "MC2 Final And Resistance", "MC3 Auto Appearance"]
                        machines = []
                        for idx, d in enumerate(dirs):
                            name = default_names[idx] if idx < len(default_names) else f"MC{idx + 1}"
                            machines.append({"name": name, "remote_dir": d})
                        if not machines:
                            machines.append({"name": "MC1", "remote_dir": "/"})
                        plc["machines"] = machines
                        needs_save = True

                    # Ensure date_filter schema exists
                    if "date_filter" not in plc:
                        plc["date_filter"] = {"mode": "all", "start_date": "", "end_date": ""}
                        needs_save = True

                    # Ensure ftp_mode exists
                    if "ftp_mode" not in plc:
                        plc["ftp_mode"] = "auto"
                        needs_save = True
                
                # Ensure target_directory has a default if empty
                if not data.get("global_settings", {}).get("target_directory", "").strip():
                    if "global_settings" not in data:
                        data["global_settings"] = {}
                    data["global_settings"]["target_directory"] = DEFAULT_TARGET_DIR
                    needs_save = True

                if needs_save:
                    self.config = data
                    self.save_config()
                return data
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG

    def save_config(self, config_data=None):
        if config_data is not None:
            self.config = config_data
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self):
        return self.config

    def update_global_settings(self, settings):
        self.config["global_settings"].update(settings)
        self.save_config()

    def add_plc(self, plc_data):
        self.config["plcs"].append(plc_data)
        self.save_config()

    def update_plc(self, index, plc_data):
        if 0 <= index < len(self.config["plcs"]):
            self.config["plcs"][index] = plc_data
            self.save_config()

    def delete_plc(self, index):
        if 0 <= index < len(self.config["plcs"]):
            del self.config["plcs"][index]
            self.save_config()

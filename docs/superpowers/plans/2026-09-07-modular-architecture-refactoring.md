# Modular Clean Architecture Refactoring & FTP Folder Browser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the monolithic desktop FTP transfer application into a modular, clean architecture with single-responsibility layers, automatic path sanitization, robust persistent logging, and an interactive remote FTP folder browser.

**Architecture:** Layered architecture separating `core/` (services, path utilities, FTP client, logging, configuration) from `ui/` (CustomTkinter views, reusable components, and main app container), with root-level shims for 100% backward compatibility.

**Tech Stack:** Python 3.9+, CustomTkinter 5.2.2, ftplib, Nuitka.

## Global Constraints

- Preserve exact existing `config.json` schema and compatibility.
- Ensure all GUI actions remain non-blocking via daemon threads.
- All remote directory paths sent to FTP must be normalized (forward slashes `/`, no Windows drive letters `C:`).
- Keep root-level compatibility shims for `gui.py`, `ftp_client.py`, and `config_manager.py`.
- Ensure Nuitka packaging scripts (`build.bat` and `build_quick.bat`) continue to compile `FTP_Control.exe` without error.

---

### Task 1: Core Path Utilities & Unit Tests

**Files:**
- Create: `core/__init__.py`
- Create: `core/path_utils.py`
- Test: `tests/test_path_utils.py`

**Interfaces:**
- Produces:
  - `sanitize_remote_path(path: str) -> str`
  - `format_local_save_dir(base_dir: str, plc_name: str, sub_dir: str = "", separate_by_date: bool = True) -> Path`

- [ ] **Step 1: Write unit tests for path utilities**

Create `tests/test_path_utils.py`:
```python
import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.path_utils import sanitize_remote_path, format_local_save_dir

def test_sanitize_remote_path():
    # Windows drive letter stripping
    assert sanitize_remote_path(r"C:\Users\user\Documents\TEST") == "/Users/user/Documents/TEST"
    assert sanitize_remote_path("D:/Data/Logs") == "/Data/Logs"
    # Backslash conversion
    assert sanitize_remote_path(r"\0_CARD\log0") == "/0_CARD/log0"
    assert sanitize_remote_path(r"0_CARD\log0\") == "/0_CARD/log0"
    # Consecutive slash normalization
    assert sanitize_remote_path("//0_CARD///log0//") == "/0_CARD/log0"
    # Empty or root
    assert sanitize_remote_path("") == "/"
    assert sanitize_remote_path("/") == "/"
    assert sanitize_remote_path("   ") == "/"

def test_format_local_save_dir(tmp_path):
    target = tmp_path / "downloads"
    p = format_local_save_dir(str(target), "PLC_1", "MC1", separate_by_date=False)
    assert p == target / "PLC_1" / "MC1"
    assert p.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 tests/test_path_utils.py` (or using pytest)
Expected: FAIL with ModuleNotFoundError: No module named 'core.path_utils'

- [ ] **Step 3: Implement `core/path_utils.py`**

Create `core/__init__.py` and `core/path_utils.py`:
```python
import re
import datetime
from pathlib import Path

def sanitize_remote_path(path_str: str) -> str:
    """
    Sanitize remote path for FTP navigation:
    - Strips leading/trailing whitespace
    - Strips Windows drive letter (e.g. C:, D:)
    - Replaces backslashes with forward slashes
    - Collapses multiple slashes into single slash
    - Ensures leading slash and strips trailing slash (unless root /)
    """
    if not path_str or not path_str.strip():
        return "/"
    
    cleaned = path_str.strip()
    # Strip Windows drive letter like C: or c:
    cleaned = re.sub(r'^[a-zA-Z]:', '', cleaned)
    # Convert backslashes to forward slashes
    cleaned = cleaned.replace('\\', '/')
    # Collapse multiple consecutive slashes
    cleaned = re.sub(r'/+', '/', cleaned)
    # Strip trailing slash if longer than 1 character
    if len(cleaned) > 1 and cleaned.endswith('/'):
        cleaned = cleaned[:-1]
    # Ensure leading slash
    if not cleaned.startswith('/'):
        cleaned = '/' + cleaned
        
    return cleaned

def format_local_save_dir(base_dir: str, plc_name: str, sub_dir: str = "", separate_by_date: bool = True) -> Path:
    """
    Format local save directory and create parent folders if they don't exist.
    """
    target = Path(base_dir) / plc_name
    if sub_dir:
        target = target / sub_dir
    if separate_by_date:
        date_str = datetime.datetime.now().strftime("%d-%m-%Y")
        target = target / date_str
        
    target.mkdir(parents=True, exist_ok=True)
    return target
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.12 tests/test_path_utils.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/__init__.py core/path_utils.py tests/test_path_utils.py
git commit -m "feat(core): add path utilities with sanitization and tests"
```

---

### Task 2: Core Logger & Configuration Service

**Files:**
- Create: `core/logger.py`
- Create: `core/config_service.py`
- Test: `tests/test_config_and_logger.py`

**Interfaces:**
- Consumes: `core/path_utils.py`
- Produces:
  - `AppLogger`: `log(msg, level="info")`, `register_callback(fn)`, `unregister_callback(fn)`
  - `ConfigManager`: `get()`, `save_config()`, `update_global_settings(settings)`, `add_plc(plc)`, `update_plc(idx, plc)`, `delete_plc(idx)`

- [ ] **Step 1: Write test for ConfigManager and AppLogger**

Create `tests/test_config_and_logger.py`:
```python
import os
import sys
import json
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.config_service import ConfigManager
from core.logger import AppLogger

def test_config_crud(tmp_path):
    config_file = tmp_path / "test_config.json"
    mgr = ConfigManager(str(config_file))
    cfg = mgr.get()
    assert "global_settings" in cfg
    assert len(cfg["plcs"]) == 0
    
    # Add PLC
    mgr.add_plc({"name": "Test PLC", "host": "127.0.0.1"})
    assert len(mgr.get()["plcs"]) == 1
    
    # Update PLC
    mgr.update_plc(0, {"name": "Updated PLC", "host": "127.0.0.1"})
    assert mgr.get()["plcs"][0]["name"] == "Updated PLC"
    
    # Delete PLC
    mgr.delete_plc(0)
    assert len(mgr.get()["plcs"]) == 0

def test_logger_callback():
    logs = []
    logger = AppLogger()
    cb = lambda msg, level: logs.append((msg, level))
    logger.register_callback(cb)
    logger.info("Test Info")
    logger.error("Test Error")
    logger.unregister_callback(cb)
    assert len(logs) == 2
    assert logs[0][1] == "info"
    assert logs[1][1] == "error"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 tests/test_config_and_logger.py`
Expected: FAIL

- [ ] **Step 3: Implement `core/logger.py` and `core/config_service.py`**

Create `core/logger.py`:
```python
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
        
        # Determine log level for file
        lower = level.lower()
        if lower == "error":
            self.file_logger.error(message)
        elif lower == "warning":
            self.file_logger.warning(message)
        else:
            self.file_logger.info(message)

        # Notify UI callbacks
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
```

Create `core/config_service.py`:
```python
import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "global_settings": {
        "target_directory": "",
        "file_extensions": [".csv", ".txt"],
        "separate_by_date": True,
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.12 tests/test_config_and_logger.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/logger.py core/config_service.py tests/test_config_and_logger.py
git commit -m "feat(core): implement central logger and config service"
```

---

### Task 3: Core FTP Service & Remote Directory Explorer

**Files:**
- Create: `core/ftp_service.py`
- Test: `tests/test_ftp_service.py`

**Interfaces:**
- Consumes: `core/path_utils.py`, `core/logger.py`
- Produces:
  - `list_remote_directories(host, port, username, password, current_dir="/", timeout=10) -> (bool, list[str] | str)`
  - `test_connection(host, port, username, password, timeout=5) -> (bool, str)`
  - `FTPDownloader` class: `connect()`, `download_files()`, `stop()`

- [ ] **Step 1: Write integration test for FTP service**

Create `tests/test_ftp_service.py`:
```python
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.ftp_service import list_remote_directories, test_connection

def test_ftp_listing_live():
    # Tests against local running FTP server if active
    ok, dirs_or_err = list_remote_directories("192.168.1.169", 21, "user", "156900", "/")
    if ok:
        assert isinstance(dirs_or_err, list)
        assert "Documents" in dirs_or_err
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 tests/test_ftp_service.py`
Expected: FAIL

- [ ] **Step 3: Implement `core/ftp_service.py`**

Create `core/ftp_service.py`:
```python
import ftplib
import os
import io
from pathlib import Path
from contextlib import redirect_stdout
from core.path_utils import sanitize_remote_path, format_local_save_dir
from core.logger import logger

def test_connection(host: str, port: int, username: str, password: str, timeout: int = 5) -> tuple[bool, str]:
    """Test FTP connection and login."""
    try:
        ftp = ftplib.FTP()
        ftp.connect(host, int(port), timeout=timeout)
        ftp.login(username, password)
        ftp.quit()
        return True, "Connected successfully."
    except Exception as e:
        if '530' in str(e):
            return False, "530 Not logged in (Username or Password incorrect)."
        return False, str(e)

def list_remote_directories(host: str, port: int, username: str, password: str, current_dir: str = "/", timeout: int = 10) -> tuple[bool, list[str] | str]:
    """List subdirectories in current_dir on remote FTP server."""
    clean_dir = sanitize_remote_path(current_dir)
    try:
        ftp = ftplib.FTP()
        ftp.connect(host, int(port), timeout=timeout)
        ftp.login(username, password)
        ftp.cwd(clean_dir)
        
        dir_names = []
        lines = []
        ftp.dir(lines.append)
        
        # Parse MLSD or standard LIST output for directories
        for line in lines:
            parts = line.split()
            if not parts:
                continue
            # Windows/DOS format: "09-05-26  09:04AM       <DIR>          Documents"
            if "<DIR>" in parts:
                dir_idx = parts.index("<DIR>")
                name = " ".join(parts[dir_idx + 1:])
                if name not in [".", ".."]:
                    dir_names.append(name)
            # Unix format: "drwxr-xr-x ..."
            elif parts[0].startswith('d'):
                name = " ".join(parts[8:])
                if name not in [".", ".."]:
                    dir_names.append(name)
                    
        # Fallback: if dir parsing found nothing, try checking nlst items
        if not dir_names:
            try:
                for item in ftp.nlst():
                    if item in [".", ".."]:
                        continue
                    try:
                        ftp.cwd(f"{clean_dir.rstrip('/')}/{item}")
                        dir_names.append(item)
                        ftp.cwd(clean_dir)
                    except Exception:
                        pass
            except Exception:
                pass

        ftp.quit()
        return True, sorted(dir_names)
    except Exception as e:
        return False, f"Failed to list directory: {e}"

class FTPDownloader:
    def __init__(self, host, port, username, password, remote_dirs, local_target_dir, file_extensions, separate_by_date, plc_name):
        self.host = host
        self.port = int(port)
        self.username = username
        self.password = password
        self.remote_dirs = [sanitize_remote_path(d) for d in remote_dirs if d.strip()]
        self.local_target_dir = local_target_dir
        self.file_extensions = [ext.lower() for ext in file_extensions]
        self.separate_by_date = separate_by_date
        self.plc_name = plc_name
        self.ftp = None
        self.is_running = False

    def connect(self, log_callback=None) -> tuple[bool, str]:
        debug_output = io.StringIO()
        try:
            self.ftp = ftplib.FTP()
            self.ftp.set_debuglevel(1)
            with redirect_stdout(debug_output):
                self.ftp.connect(self.host, self.port, timeout=10)
                self.ftp.login(self.username, self.password)
            self.ftp.set_debuglevel(0)
            return True, "Connected successfully."
        except Exception as e:
            debug_log = debug_output.getvalue()
            if log_callback and debug_log:
                log_callback(f"[{self.plc_name}] --- FTP Debug Log Start ---\n{debug_log}[{self.plc_name}] --- FTP Debug Log End ---")
            if '530' in str(e):
                return False, f"Connection failed: 530 Not logged in. (Username or Password incorrect)"
            return False, f"Connection failed: {e}"

    def disconnect(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except Exception:
                try:
                    self.ftp.close()
                except Exception:
                    pass
            self.ftp = None

    def download_files(self, progress_callback=None, log_callback=None) -> bool:
        self.is_running = True
        success, msg = self.connect(log_callback)
        if not success:
            if log_callback:
                log_callback(f"[{self.plc_name}] {msg}")
            self.is_running = False
            return False

        try:
            files_by_dir = {}
            total_target_files = []
            for r_dir in self.remote_dirs:
                if not self.is_running:
                    break
                try:
                    self.ftp.cwd(r_dir)
                    files = self.ftp.nlst()
                    t_files = [f for f in files if any(f.lower().endswith(ext) for ext in self.file_extensions)]
                    files_by_dir[r_dir] = t_files
                    total_target_files.extend(t_files)
                except Exception as e:
                    if log_callback:
                        log_callback(f"[{self.plc_name}] Error accessing {r_dir}: {e}")

            if not total_target_files:
                if log_callback:
                    log_callback(f"[{self.plc_name}] No matching files found in any directory.")
                self.disconnect()
                self.is_running = False
                return True

            total_files = len(total_target_files)
            current_index = 0
            dir_index = 1
            
            mc_names = {
                1: "MC1 Connector Leak",
                2: "MC2 Final And Resistance",
                3: "MC3 Auto Appearance"
            }

            for r_dir, t_files in files_by_dir.items():
                if not self.is_running:
                    break
                sub_dir = mc_names.get(dir_index, f"MC{dir_index}")
                save_dir = format_local_save_dir(self.local_target_dir, self.plc_name, sub_dir, self.separate_by_date)
                dir_index += 1

                try:
                    self.ftp.cwd(r_dir)
                except Exception:
                    continue

                for filename in t_files:
                    if not self.is_running:
                        if log_callback:
                            log_callback(f"[{self.plc_name}] Download stopped by user.")
                        break

                    pure_filename = Path(filename).name
                    local_filepath = save_dir / pure_filename

                    # Incremental check: if file already exists with same size, skip
                    try:
                        remote_size = self.ftp.size(filename)
                        if local_filepath.exists() and remote_size and local_filepath.stat().st_size == remote_size:
                            current_index += 1
                            if progress_callback:
                                progress_callback(current_index, total_files)
                            continue
                    except Exception:
                        pass

                    try:
                        with open(local_filepath, 'wb') as f:
                            if log_callback:
                                log_callback(f"[{self.plc_name}] Downloading {r_dir}/{pure_filename}...")
                            self.ftp.retrbinary(f"RETR {filename}", f.write)
                        current_index += 1
                        if progress_callback:
                            progress_callback(current_index, total_files)
                    except Exception as e:
                        if log_callback:
                            log_callback(f"[{self.plc_name}] Error downloading {filename}: {e}")

            if log_callback:
                log_callback(f"[{self.plc_name}] Download process completed.")
        except Exception as e:
            if log_callback:
                log_callback(f"[{self.plc_name}] FTP Error: {e}")
        finally:
            self.disconnect()
            self.is_running = False

        return True

    def stop(self):
        self.is_running = False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.12 tests/test_ftp_service.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/ftp_service.py tests/test_ftp_service.py
git commit -m "feat(core): implement robust FTP service with directory exploration"
```

---

### Task 4: Reusable UI Components

**Files:**
- Create: `ui/__init__.py`
- Create: `ui/components/__init__.py`
- Create: `ui/components/tooltip.py`
- Create: `ui/components/log_console.py`
- Create: `ui/components/ftp_browser_dialog.py`

**Interfaces:**
- Produces:
  - `ToolTip(widget, text)`
  - `LogConsole(parent, height=150)`
  - `FTPBrowserDialog(parent, host, port, username, password, initial_dir="/", on_select_callback=None)`

- [ ] **Step 1: Implement `ui/components/tooltip.py`**

Create `ui/__init__.py`, `ui/components/__init__.py`, and `ui/components/tooltip.py`:
```python
import tkinter as tk

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tw, text=self.text, justify='left',
                         background="#333333", foreground="white", relief='solid', borderwidth=1,
                         font=("Arial", "10", "normal"))
        label.pack(ipadx=4, ipady=2)

    def leave(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None
```

- [ ] **Step 2: Implement `ui/components/log_console.py`**

Create `ui/components/log_console.py`:
```python
import customtkinter as ctk
import time

class LogConsole(ctk.CTkFrame):
    def __init__(self, master, height=150, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", pady=(5, 2))
        
        lbl = ctk.CTkLabel(top_bar, text="Log Console", font=ctk.CTkFont(weight="bold"))
        lbl.pack(side="left")
        
        btn_clear = ctk.CTkButton(top_bar, text="Clear", width=50, height=22, font=ctk.CTkFont(size=11), command=self.clear_logs)
        btn_clear.pack(side="right")
        
        self.textbox = ctk.CTkTextbox(self, height=height)
        self.textbox.pack(fill="x", expand=True)
        
        self.textbox.tag_config("error", foreground="#FF5252")
        self.textbox.tag_config("success", foreground="#00E676")
        self.textbox.tag_config("warning", foreground="#FFB74D")

    def append_message(self, message: str, level: str = None):
        tag = None
        if level:
            tag = level.lower()
        else:
            lower = message.lower()
            if "error" in lower or "fail" in lower:
                tag = "error"
            elif "warning" in lower:
                tag = "warning"
            elif "success" in lower or "ok" in lower or "completed" in lower or "finished" in lower:
                tag = "success"

        if tag in ["error", "success", "warning"]:
            self.textbox.insert("end", message + "\n", tag)
        else:
            self.textbox.insert("end", message + "\n")
        self.textbox.see("end")

    def clear_logs(self):
        self.textbox.delete("1.0", "end")
```

- [ ] **Step 3: Implement `ui/components/ftp_browser_dialog.py`**

Create `ui/components/ftp_browser_dialog.py`:
```python
import customtkinter as ctk
import threading
from core.ftp_service import list_remote_directories
from core.path_utils import sanitize_remote_path

class FTPBrowserDialog(ctk.CTkToplevel):
    def __init__(self, parent, host, port, username, password, initial_dir="/", on_select_callback=None):
        super().__init__(parent)
        self.title("📁 Browse Remote FTP Directories")
        self.geometry("520x460")
        self.minsize(450, 350)
        self.grab_set()

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.current_dir = sanitize_remote_path(initial_dir)
        self.on_select_callback = on_select_callback

        # Top Address Bar
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=15, pady=(15, 5))

        btn_up = ctk.CTkButton(nav_frame, text="⬆ Up", width=60, command=self.go_up)
        btn_up.pack(side="left", padx=(0, 5))

        self.path_entry = ctk.CTkEntry(nav_frame)
        self.path_entry.insert(0, self.current_dir)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=5)

        btn_go = ctk.CTkButton(nav_frame, text="Go", width=50, command=self.go_manual)
        btn_go.pack(side="right", padx=(5, 0))

        # Status indicator
        self.status_label = ctk.CTkLabel(self, text="Connecting...", text_color="gray")
        self.status_label.pack(anchor="w", padx=20, pady=2)

        # Folder List Frame
        self.folder_frame = ctk.CTkScrollableFrame(self, label_text="Folders")
        self.folder_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # Bottom Action Buttons
        bot_frame = ctk.CTkFrame(self, fg_color="transparent")
        bot_frame.pack(fill="x", padx=15, pady=(5, 15))

        btn_cancel = ctk.CTkButton(bot_frame, text="Cancel", width=80, fg_color="gray", hover_color="#555", command=self.destroy)
        btn_cancel.pack(side="right", padx=5)

        btn_select = ctk.CTkButton(bot_frame, text="Select This Directory", width=160, command=self.select_current)
        btn_select.pack(side="right", padx=5)

        self.load_directory(self.current_dir)

    def load_directory(self, target_dir):
        self.status_label.configure(text=f"Loading {target_dir}...", text_color="gray")
        for w in self.folder_frame.winfo_children():
            w.destroy()

        def worker():
            ok, res = list_remote_directories(self.host, self.port, self.username, self.password, target_dir)
            if ok:
                self.after(0, lambda: self._on_load_success(target_dir, res))
            else:
                self.after(0, lambda: self._on_load_fail(str(res)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_load_success(self, target_dir, folders):
        self.current_dir = target_dir
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, self.current_dir)
        self.status_label.configure(text=f"Found {len(folders)} folder(s)", text_color="#00E676")

        if not folders:
            ctk.CTkLabel(self.folder_frame, text="(No subdirectories found)", text_color="gray").pack(pady=20)
            return

        for name in folders:
            btn = ctk.CTkButton(
                self.folder_frame,
                text=f"📁 {name}",
                anchor="w",
                fg_color="transparent",
                hover_color=("#E0E0E0", "#333333"),
                text_color=("black", "white"),
                command=lambda n=name: self.navigate_into(n)
            )
            btn.pack(fill="x", padx=5, pady=2)

    def _on_load_fail(self, err_msg):
        self.status_label.configure(text=f"Error: {err_msg}", text_color="#FF5252")
        ctk.CTkLabel(self.folder_frame, text=f"Failed to access directory:\n{err_msg}", text_color="#FF5252").pack(pady=20)

    def navigate_into(self, folder_name):
        new_path = sanitize_remote_path(f"{self.current_dir.rstrip('/')}/{folder_name}")
        self.load_directory(new_path)

    def go_up(self):
        if self.current_dir in ["/", ""]:
            return
        parent = sanitize_remote_path("/".join(self.current_dir.rstrip("/").split("/")[:-1]))
        if not parent:
            parent = "/"
        self.load_directory(parent)

    def go_manual(self):
        entered = sanitize_remote_path(self.path_entry.get())
        self.load_directory(entered)

    def select_current(self):
        if self.on_select_callback:
            self.on_select_callback(self.current_dir)
        self.destroy()
```

- [ ] **Step 4: Commit components**

```bash
git add ui/__init__.py ui/components/__init__.py ui/components/tooltip.py ui/components/log_console.py ui/components/ftp_browser_dialog.py
git commit -m "feat(ui): add tooltip, log console, and FTP remote folder browser components"
```

---

### Task 5: UI Views Implementation

**Files:**
- Create: `ui/views/__init__.py`
- Create: `ui/views/settings_view.py`
- Create: `ui/views/plc_manager_view.py`
- Create: `ui/views/dashboard_view.py`

**Interfaces:**
- Consumes: `core/config_service.py`, `core/ftp_service.py`, `ui/components/`
- Produces:
  - `SettingsView`: frame for global config
  - `PLCManagerView`: frame for CRUD of PLCs with FTP Browser integration
  - `DashboardView`: overview frame with PLC cards, test button, progress, cooldown, download all

- [ ] **Step 1: Implement `ui/views/settings_view.py`**

Create `ui/views/__init__.py` and `ui/views/settings_view.py`:
```python
import customtkinter as ctk
from tkinter import filedialog

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, config_manager, on_settings_changed=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.on_settings_changed = on_settings_changed
        self.config = self.config_manager.get()
        self.build_view()

    def build_view(self):
        header = ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=10, pady=(10, 30), sticky="w")
        
        # Target Directory
        ctk.CTkLabel(self, text="Target Save Directory:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.target_dir_var = ctk.StringVar(value=self.config["global_settings"].get("target_directory", ""))
        self.target_dir_entry = ctk.CTkEntry(self, textvariable=self.target_dir_var, width=320)
        self.target_dir_entry.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        btn_browse = ctk.CTkButton(self, text="Browse", width=80, command=self.browse_target_dir)
        btn_browse.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # File Extensions
        ctk.CTkLabel(self, text="File Extensions (comma separated, e.g. .csv,.txt):").grid(row=3, column=0, padx=10, pady=(20, 5), sticky="w")
        exts = self.config["global_settings"].get("file_extensions", [])
        self.ext_var = ctk.StringVar(value=",".join(exts))
        self.ext_entry = ctk.CTkEntry(self, textvariable=self.ext_var, width=320)
        self.ext_entry.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        
        # Separate by Date
        self.date_var = ctk.BooleanVar(value=self.config["global_settings"].get("separate_by_date", True))
        self.date_check = ctk.CTkCheckBox(self, text="Automatically create folders by Date (e.g. 07-09-2026)", variable=self.date_var)
        self.date_check.grid(row=5, column=0, padx=10, pady=(20, 5), sticky="w")
        
        # Auto Pull Interval
        ctk.CTkLabel(self, text="Auto Pull Interval (Minutes) [0 = Disable]:").grid(row=6, column=0, padx=10, pady=(20, 5), sticky="w")
        self.interval_var = ctk.StringVar(value=str(self.config["global_settings"].get("auto_pull_interval_minutes", 60)))
        self.interval_entry = ctk.CTkEntry(self, textvariable=self.interval_var, width=100)
        self.interval_entry.grid(row=7, column=0, padx=10, pady=5, sticky="w")
        
        # Save Button
        btn_save = ctk.CTkButton(self, text="Save Settings", font=ctk.CTkFont(weight="bold"), command=self.save_settings)
        btn_save.grid(row=8, column=0, padx=10, pady=30, sticky="w")

    def browse_target_dir(self):
        dir_name = filedialog.askdirectory()
        if dir_name:
            self.target_dir_var.set(dir_name)

    def save_settings(self):
        exts = [e.strip() for e in self.ext_var.get().split(",") if e.strip()]
        settings = {
            "target_directory": self.target_dir_var.get(),
            "file_extensions": exts,
            "separate_by_date": self.date_var.get(),
            "auto_pull_interval_minutes": int(self.interval_var.get() if self.interval_var.get().isdigit() else 0)
        }
        self.config_manager.update_global_settings(settings)
        if self.on_settings_changed:
            self.on_settings_changed()
            
        saved_lbl = ctk.CTkLabel(self, text="Settings Saved Successfully!", text_color="#00E676")
        saved_lbl.grid(row=8, column=1, padx=10, pady=30, sticky="w")
        self.after(3000, saved_lbl.destroy)
```

- [ ] **Step 2: Implement `ui/views/plc_manager_view.py` with FTP Browser button**

Create `ui/views/plc_manager_view.py`:
```python
import customtkinter as ctk
import threading
from core.ftp_service import test_connection
from ui.components.ftp_browser_dialog import FTPBrowserDialog

class PLCManagerView(ctk.CTkFrame):
    def __init__(self, master, config_manager, on_plc_list_updated=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.on_plc_list_updated = on_plc_list_updated
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkLabel(self, text="PLC Manager", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.plc_list_frame = ctk.CTkScrollableFrame(self)
        self.plc_list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        add_btn = ctk.CTkButton(self, text="Add New PLC", font=ctk.CTkFont(weight="bold"), command=self.open_plc_dialog)
        add_btn.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        self.refresh_list()

    def refresh_list(self):
        for w in self.plc_list_frame.winfo_children():
            w.destroy()
            
        header_frame = ctk.CTkFrame(self.plc_list_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        header_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        header_frame.grid_columnconfigure(4, weight=0, minsize=140)
        
        headers = ["Name", "Host:Port", "Username", "Remote Directories", "Actions"]
        for col, text in enumerate(headers):
            anchor = "e" if col == 4 else "w"
            ctk.CTkLabel(header_frame, text=text, font=ctk.CTkFont(weight="bold")).grid(row=0, column=col, padx=10, pady=5, sticky=anchor)
            
        sep = ctk.CTkFrame(self.plc_list_frame, height=2, fg_color=("gray70", "gray30"))
        sep.pack(fill="x", padx=5, pady=(0, 5))
        
        plcs = self.config_manager.get().get("plcs", [])
        for i, plc in enumerate(plcs):
            frame = ctk.CTkFrame(self.plc_list_frame)
            frame.pack(fill="x", padx=5, pady=2)
            frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
            frame.grid_columnconfigure(4, weight=0, minsize=140)
            
            ctk.CTkLabel(frame, text=plc.get('name', '')).grid(row=0, column=0, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(frame, text=f"{plc.get('host', '')}:{plc.get('port', 21)}").grid(row=0, column=1, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(frame, text=plc.get('username', '')).grid(row=0, column=2, padx=10, pady=10, sticky="w")
            
            r_dir = plc.get('remote_directory', '')
            display_rdir = r_dir if len(r_dir) <= 30 else r_dir[:27] + "..."
            ctk.CTkLabel(frame, text=display_rdir).grid(row=0, column=3, padx=10, pady=10, sticky="w")
            
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.grid(row=0, column=4, padx=10, pady=5, sticky="e")
            
            edit_btn = ctk.CTkButton(btn_frame, text="Edit", width=60, command=lambda idx=i: self.open_plc_dialog(idx))
            edit_btn.pack(side="left", padx=(0, 5))
            
            del_btn = ctk.CTkButton(btn_frame, text="Delete", fg_color="#d32f2f", hover_color="#b71c1c", width=60, command=lambda idx=i: self.delete_plc(idx))
            del_btn.pack(side="left")

    def delete_plc(self, index):
        self.config_manager.delete_plc(index)
        self.refresh_list()
        if self.on_plc_list_updated:
            self.on_plc_list_updated()

    def open_plc_dialog(self, edit_index=None):
        dialog = ctk.CTkToplevel(self)
        is_edit = edit_index is not None
        dialog.title("Edit PLC" if is_edit else "Add PLC")
        dialog.geometry("450x540")
        dialog.grab_set()
        
        plcs = self.config_manager.get().get("plcs", [])
        plc_data = plcs[edit_index] if is_edit and edit_index < len(plcs) else {}
        
        ctk.CTkLabel(dialog, text="PLC Name:").pack(pady=(12, 0))
        name_entry = ctk.CTkEntry(dialog, width=280)
        name_entry.insert(0, plc_data.get("name", ""))
        name_entry.pack()
        
        ctk.CTkLabel(dialog, text="IP Address (Host):").pack(pady=(5, 0))
        host_entry = ctk.CTkEntry(dialog, width=280)
        host_entry.insert(0, plc_data.get("host", ""))
        host_entry.pack()
        
        ctk.CTkLabel(dialog, text="Port:").pack(pady=(5, 0))
        port_entry = ctk.CTkEntry(dialog, width=280)
        port_entry.insert(0, str(plc_data.get("port", 21)))
        port_entry.pack()
        
        ctk.CTkLabel(dialog, text="Username:").pack(pady=(5, 0))
        user_entry = ctk.CTkEntry(dialog, width=280)
        user_entry.insert(0, plc_data.get("username", "ftp"))
        user_entry.pack()
        
        ctk.CTkLabel(dialog, text="Password:").pack(pady=(5, 0))
        pass_entry = ctk.CTkEntry(dialog, width=280, show="*")
        pass_entry.insert(0, plc_data.get("password", ""))
        pass_entry.pack()
        
        ctk.CTkLabel(dialog, text="Remote Dirs (comma separated):").pack(pady=(5, 0))
        dir_entry = ctk.CTkEntry(dialog, width=280)
        dir_entry.insert(0, plc_data.get("remote_directory", "/0_CARD/log0/,/0_CARD/log1/,/0_CARD/log2/"))
        dir_entry.pack()

        # Tools row: Test Connection and Browse FTP
        tools_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        tools_frame.pack(pady=8)
        
        test_status_lbl = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=11))
        test_status_lbl.pack()

        def do_test():
            h = host_entry.get().strip()
            p = int(port_entry.get() if port_entry.get().isdigit() else 21)
            u = user_entry.get().strip()
            pw = pass_entry.get().strip()
            test_status_lbl.configure(text="Testing connection...", text_color="gray")
            
            def run():
                ok, msg = test_connection(h, p, u, pw)
                if ok:
                    dialog.after(0, lambda: test_status_lbl.configure(text="✓ Connection Successful!", text_color="#00E676"))
                else:
                    dialog.after(0, lambda: test_status_lbl.configure(text=f"✗ {msg}", text_color="#FF5252"))
            threading.Thread(target=run, daemon=True).start()

        def open_ftp_browser():
            h = host_entry.get().strip()
            p = int(port_entry.get() if port_entry.get().isdigit() else 21)
            u = user_entry.get().strip()
            pw = pass_entry.get().strip()
            if not h:
                test_status_lbl.configure(text="Please enter Host/IP first.", text_color="#FF5252")
                return
            
            # Callback when user picks a directory in browser
            def on_dir_selected(chosen_dir):
                current_text = dir_entry.get().strip()
                if not current_text or current_text.startswith("/0_CARD/"):
                    dir_entry.delete(0, "end")
                    dir_entry.insert(0, chosen_dir)
                else:
                    # Append or replace
                    dir_entry.delete(0, "end")
                    dir_entry.insert(0, chosen_dir)
            
            init_d = dir_entry.get().split(",")[0].strip() if dir_entry.get().strip() else "/"
            FTPBrowserDialog(dialog, h, p, u, pw, initial_dir=init_d, on_select_callback=on_dir_selected)

        btn_test = ctk.CTkButton(tools_frame, text="🔌 Test Connection", width=130, command=do_test)
        btn_test.pack(side="left", padx=5)

        btn_browse_ftp = ctk.CTkButton(tools_frame, text="📁 Browse FTP...", width=130, command=open_ftp_browser)
        btn_browse_ftp.pack(side="left", padx=5)

        def save():
            new_data = {
                "name": name_entry.get().strip(),
                "host": host_entry.get().strip(),
                "port": int(port_entry.get() if port_entry.get().isdigit() else 21),
                "username": user_entry.get().strip(),
                "password": pass_entry.get().strip(),
                "remote_directory": dir_entry.get().strip()
            }
            if new_data["name"] and new_data["host"]:
                if is_edit:
                    self.config_manager.update_plc(edit_index, new_data)
                else:
                    self.config_manager.add_plc(new_data)
                self.refresh_list()
                if self.on_plc_list_updated:
                    self.on_plc_list_updated()
                dialog.destroy()

        ctk.CTkButton(dialog, text="Save PLC", font=ctk.CTkFont(weight="bold"), command=save).pack(pady=(15, 20))
```

- [ ] **Step 3: Implement `ui/views/dashboard_view.py`**

Create `ui/views/dashboard_view.py`:
```python
import customtkinter as ctk
import threading
from core.ftp_service import test_connection, FTPDownloader
from core.logger import logger
from ui.components.tooltip import ToolTip
from ui.components.log_console import LogConsole

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, config_manager, request_timer_reset_cb=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.request_timer_reset_cb = request_timer_reset_cb
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkLabel(self, text="Download Overview", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.scrollable_plc_frame = ctk.CTkScrollableFrame(self, label_text="Connected PLCs")
        self.scrollable_plc_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Log Console Component
        self.log_console = LogConsole(self, height=150)
        self.log_console.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        logger.register_callback(self.log_console.append_message)
        
        # Bottom controls
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        self.btn_download_all = ctk.CTkButton(btn_frame, text="Download All", font=ctk.CTkFont(weight="bold"), text_color="white", command=self.download_all)
        self.btn_download_all.pack(side="left", padx=5)
        
        self.cooldown_label = ctk.CTkLabel(btn_frame, text="", text_color="gray", font=ctk.CTkFont(weight="bold"))
        self.cooldown_label.pack(side="left", padx=10)
        
        self.refresh_plcs()

    def refresh_plcs(self):
        for w in self.scrollable_plc_frame.winfo_children():
            w.destroy()
            
        plcs = self.config_manager.get().get("plcs", [])
        for plc in plcs:
            frame = ctk.CTkFrame(self.scrollable_plc_frame)
            frame.pack(fill="x", padx=5, pady=5)
            
            lbl = ctk.CTkLabel(frame, text=f"{plc['name']} ({plc['host']})", font=ctk.CTkFont(weight="bold"))
            lbl.pack(side="left", padx=10, pady=10)
            
            small_btn = ctk.CTkButton(frame, text="🔌", width=30, height=30)
            small_btn.pack(side="left", padx=5, pady=10)
            ToolTip(small_btn, "Test Connection")
            
            pb = ctk.CTkProgressBar(frame, width=150)
            pb.set(0)
            pb.pack(side="left", padx=20, pady=10)
            
            status = ctk.CTkLabel(frame, text="Ready")
            status.pack(side="left", padx=10, pady=10)
            
            small_btn.configure(command=lambda p=plc, stat=status: self.test_single_connection(p, stat))
            
            btn = ctk.CTkButton(frame, text="Download", font=ctk.CTkFont(weight="bold"), text_color="white",
                                command=lambda p=plc, progress=pb, stat=status: self.download_single(p, progress, stat))
            btn.pack(side="right", padx=10, pady=10)

    def test_single_connection(self, plc_data, status_label):
        def run():
            status_label.configure(text="Testing...")
            ok, msg = test_connection(plc_data['host'], int(plc_data.get('port', 21)), plc_data['username'], plc_data['password'])
            if ok:
                status_label.configure(text="Conn OK")
                logger.success(f"[{plc_data['name']}] Connection Test: Success")
            else:
                status_label.configure(text="Conn Fail")
                logger.error(f"[{plc_data['name']}] Connection Test: Failed ({msg})")
        threading.Thread(target=run, daemon=True).start()

    def download_single(self, plc_data, progress_bar, status_label):
        g_settings = self.config_manager.get()["global_settings"]
        target_dir = g_settings.get("target_directory", "")
        if not target_dir:
            logger.error(f"[{plc_data['name']}] Target directory not configured in Settings.")
            return

        r_dirs_raw = plc_data.get('remote_directory', '')
        remote_dirs = [d.strip() for d in r_dirs_raw.split(',') if d.strip()]
        
        downloader = FTPDownloader(
            host=plc_data['host'],
            port=plc_data.get('port', 21),
            username=plc_data['username'],
            password=plc_data['password'],
            remote_dirs=remote_dirs,
            local_target_dir=target_dir,
            file_extensions=g_settings.get("file_extensions", [".csv", ".txt"]),
            separate_by_date=g_settings.get("separate_by_date", True),
            plc_name=plc_data['name']
        )

        def update_progress(current, total):
            prog = current / total if total > 0 else 0
            self.after(0, lambda: progress_bar.set(prog))
            self.after(0, lambda: status_label.configure(text=f"{current}/{total}"))

        def log_cb(msg):
            self.after(0, lambda: logger.info(msg))

        def run():
            self.after(0, lambda: status_label.configure(text="Connecting..."))
            self.after(0, lambda: progress_bar.set(0))
            logger.info(f"Starting download for {plc_data['name']}...")
            downloader.download_files(progress_callback=update_progress, log_callback=log_cb)
            self.after(0, lambda: status_label.configure(text="Finished"))

        threading.Thread(target=run, daemon=True).start()

    def download_all(self):
        for widget in self.scrollable_plc_frame.winfo_children():
            btn = [w for w in widget.winfo_children() if isinstance(w, ctk.CTkButton) and w.cget("text") == "Download"]
            if btn:
                btn[0].invoke()
        if self.request_timer_reset_cb:
            self.request_timer_reset_cb()
```

- [ ] **Step 4: Commit views**

```bash
git add ui/views/__init__.py ui/views/settings_view.py ui/views/plc_manager_view.py ui/views/dashboard_view.py
git commit -m "feat(ui): implement Dashboard, PLC Manager, and Settings views"
```

---

### Task 6: Main App Integration & Compatibility Shims

**Files:**
- Create: `ui/app.py`
- Modify: `main.py`
- Modify: `gui.py`
- Modify: `ftp_client.py`
- Modify: `config_manager.py`

- [ ] **Step 1: Implement `ui/app.py`**

Create `ui/app.py`:
```python
import customtkinter as ctk
import tkinter as tk
import time
import os
import sys
from core.config_service import ConfigManager
from ui.views.dashboard_view import DashboardView
from ui.views.plc_manager_view import PLCManagerView
from ui.views.settings_view import SettingsView

# Apply Purple Theme overrides
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
if "CTkButton" in ctk.ThemeManager.theme:
    ctk.ThemeManager.theme["CTkButton"]["fg_color"] = ["#7B1FA2", "#7B1FA2"]
    ctk.ThemeManager.theme["CTkButton"]["hover_color"] = ["#4A148C", "#4A148C"]
if "CTkProgressBar" in ctk.ThemeManager.theme:
    ctk.ThemeManager.theme["CTkProgressBar"]["progress_color"] = ["#7B1FA2", "#7B1FA2"]
if "CTkOptionMenu" in ctk.ThemeManager.theme:
    ctk.ThemeManager.theme["CTkOptionMenu"]["fg_color"] = ["#7B1FA2", "#7B1FA2"]
    ctk.ThemeManager.theme["CTkOptionMenu"]["button_color"] = ["#4A148C", "#4A148C"]
    ctk.ThemeManager.theme["CTkOptionMenu"]["button_hover_color"] = ["#311B92", "#311B92"]

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FTP Get Data Record Process Critical Control")
        self.geometry("920x620")
        self.minsize(820, 520)

        def resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            return os.path.join(base_path, relative_path)

        icon_path = resource_path("app_icon.png")
        if os.path.exists(icon_path):
            try:
                self.icon_img = tk.PhotoImage(file=icon_path)
                self.after(200, lambda: self.iconphoto(False, self.icon_img))
            except Exception:
                pass

        self.config_manager = ConfigManager()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="FTP Control", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Overview", command=self.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_plcs = ctk.CTkButton(self.sidebar_frame, text="PLC Manager", command=self.show_plc_manager)
        self.btn_plcs.grid(row=2, column=0, padx=20, pady=10)

        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="Settings", command=self.show_settings)
        self.btn_settings.grid(row=3, column=0, padx=20, pady=10)

        # Views
        self.dashboard_view = DashboardView(self, self.config_manager, request_timer_reset_cb=self.start_auto_pull_timer)
        self.plc_manager_view = PLCManagerView(self, self.config_manager, on_plc_list_updated=self.dashboard_view.refresh_plcs)
        self.settings_view = SettingsView(self, self.config_manager, on_settings_changed=self.on_settings_saved)

        self.show_dashboard()

        # Auto pull timer
        self.next_pull_time = 0
        self.auto_pull_job = None
        self.start_auto_pull_timer()
        self.update_cooldown_ui()

        # Version
        self.version_label = ctk.CTkLabel(self, text="v1.1.0", text_color="gray", font=ctk.CTkFont(size=12))
        self.version_label.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-10)
        self.version_label.lift()

    def select_view(self, view):
        self.dashboard_view.grid_forget()
        self.plc_manager_view.grid_forget()
        self.settings_view.grid_forget()
        view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_dashboard(self):
        self.select_view(self.dashboard_view)
        self.dashboard_view.refresh_plcs()

    def show_plc_manager(self):
        self.select_view(self.plc_manager_view)
        self.plc_manager_view.refresh_list()

    def show_settings(self):
        self.select_view(self.settings_view)

    def on_settings_saved(self):
        self.start_auto_pull_timer()

    def start_auto_pull_timer(self):
        if self.auto_pull_job is not None:
            self.after_cancel(self.auto_pull_job)
            self.auto_pull_job = None

        interval_mins = self.config_manager.get()["global_settings"].get("auto_pull_interval_minutes", 60)
        if interval_mins > 0:
            interval_ms = interval_mins * 60 * 1000
            self.next_pull_time = time.time() + (interval_ms / 1000.0)
            self.auto_pull_job = self.after(interval_ms, self.trigger_auto_pull)
        else:
            self.next_pull_time = 0
            self.dashboard_view.cooldown_label.configure(text="Auto Pull: Disabled")

    def update_cooldown_ui(self):
        if self.next_pull_time > 0:
            remaining = int(self.next_pull_time - time.time())
            if remaining > 0:
                mins, secs = divmod(remaining, 60)
                self.dashboard_view.cooldown_label.configure(text=f"Next Auto Pull in: {mins:02d}:{secs:02d}")
            else:
                self.dashboard_view.cooldown_label.configure(text="Pulling...")
        self.after(1000, self.update_cooldown_ui)

    def trigger_auto_pull(self):
        self.dashboard_view.download_all()
        self.start_auto_pull_timer()
```

- [ ] **Step 2: Update `main.py`**

Update `main.py`:
```python
from ui.app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
```

- [ ] **Step 3: Update compatibility shims in `gui.py`, `ftp_client.py`, `config_manager.py`**

Update `gui.py`:
```python
from ui.app import App
from ui.components.tooltip import ToolTip
from ui.components.log_console import LogConsole

__all__ = ["App", "ToolTip", "LogConsole"]
```

Update `ftp_client.py`:
```python
from core.ftp_service import FTPDownloader, test_connection, list_remote_directories

__all__ = ["FTPDownloader", "test_connection", "list_remote_directories"]
```

Update `config_manager.py`:
```python
from core.config_service import ConfigManager, DEFAULT_CONFIG

__all__ = ["ConfigManager", "DEFAULT_CONFIG"]
```

- [ ] **Step 4: Test launching application**

Run: `py -3.12 -c "from ui.app import App; print('App module imported successfully!')"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/app.py main.py gui.py ftp_client.py config_manager.py
git commit -m "refactor: integrate modular UI app and establish backward-compatibility shims"
```

---

### Task 7: Build Verification & Documentation Update

**Files:**
- Modify: `build.bat`
- Modify: `build_quick.bat`
- Modify: `README.md`
- Modify: `SAMARY/PROJECT_SUMMARY.md`

- [ ] **Step 1: Verify and update build scripts for Nuitka**

Ensure `build.bat` and `build_quick.bat` have `--include-package=core --include-package=ui` to guarantee Nuitka includes the refactored packages.

- [ ] **Step 2: Update documentation**

Update `README.md` and `SAMARY/PROJECT_SUMMARY.md` with the new modular architecture, directory explorer feature, and path sanitization.

- [ ] **Step 3: Commit**

```bash
git add build.bat build_quick.bat README.md SAMARY/PROJECT_SUMMARY.md
git commit -m "docs: update build scripts and documentation for v1.1.0 modular architecture"
```

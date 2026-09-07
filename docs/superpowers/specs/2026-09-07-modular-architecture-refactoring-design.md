# Design Specification: Modular Clean Architecture Refactoring & FTP Folder Browser

- **Date:** 2026-09-07
- **Author:** Antigravity AI & Pair Programming Partner
- **Status:** Approved by User

---

## 1. Overview & Motivation

The **Keyence PLC Data Transfer FTP** application is a desktop utility built with Python and CustomTkinter for downloading production log files from PLCs via FTP. 

### Current Pain Points:
1. **Monolithic UI File:** `gui.py` is nearly 500 lines long, tightly coupling view layout, modal dialogs, network worker threads, cooldown timer management, and logging.
2. **Path Resolution Errors (Error 550):** Users entering Windows-style paths (e.g. `C:\Users\user\...` or backslashes `\`) trigger FTP error `550 The parameter is incorrect` because FTP servers reject Windows drive letters and require POSIX-style forward slashes.
3. **Manual Path Typing:** Users have to manually type or guess complex remote PLC directories (e.g. `/0_CARD/log0/` or `/Documents/...`) without any visual exploration tools.
4. **Lack of File Logging:** Logs are only shown in the UI textbox and are lost when the application is closed.

---

## 2. Goals & Non-Goals

### Goals:
- **Modular Layering:** Decompose the application into clean, single-responsibility modules under `core/` and `ui/`.
- **Remote FTP Folder Browser:** Provide a "📁 Browse FTP..." modal dialog in the Add/Edit PLC window so users can visually inspect the remote folder tree and pick directories with a click.
- **Robust Path Sanitizer:** Automatically sanitize remote directory inputs (strip accidental drive letters like `C:`, convert `\` to `/`, deduplicate slashes).
- **Persistent Logging:** Introduce `core/logger.py` that streams log messages to the UI console while rotating logs to `logs/app.log`.
- **100% Backward Compatibility:** Maintain root-level shims (`gui.py`, `ftp_client.py`, `config_manager.py`) and ensure Nuitka single-file executable compilation (`build.bat`) works seamlessly.

### Non-Goals:
- Rewriting the GUI in a different framework (CustomTkinter remains the UI framework).
- Changing the schema of `config.json` in a breaking manner.

---

## 3. Architecture & File Structure

```text
C:\Users\user\Desktop\Data Transfer FTP\Data Transfer FTP\
├── main.py                         # Application entry point
├── config.json                     # JSON configuration file
├── requirements.txt                # Dependencies (customtkinter, imageio)
├── build.bat                       # Nuitka full build script
├── build_quick.bat                 # Nuitka quick build script
│
├── core/                           # Business logic & services layer
│   ├── __init__.py
│   ├── path_utils.py               # Path sanitization & local directory formatting
│   ├── ftp_service.py              # FTP connection, file retrieval, directory listing
│   ├── config_service.py           # Configuration manager & schema defaults
│   └── logger.py                   # Central logger (UI callbacks + file logging)
│
├── ui/                             # Presentation layer (CustomTkinter)
│   ├── __init__.py
│   ├── app.py                      # Main App window, navigation sidebar, theme setup
│   ├── components/
│   │   ├── __init__.py
│   │   ├── tooltip.py              # Reusable widget tooltip
│   │   ├── log_console.py          # Color-coded log textbox with Clear button
│   │   └── ftp_browser_dialog.py   # Modal dialog for exploring remote FTP folders
│   └── views/
│       ├── __init__.py
│       ├── dashboard_view.py       # Overview dashboard, PLC cards, auto-pull cooldown
│       ├── plc_manager_view.py     # PLC management table, Add/Edit dialog
│       └── settings_view.py        # Global settings form & local folder picker
│
├── gui.py                          # Compatibility shim -> imports from ui.app
├── ftp_client.py                   # Compatibility shim -> imports from core.ftp_service
└── config_manager.py               # Compatibility shim -> imports from core.config_service
```

---

## 4. Detailed Component Design

### 4.1 `core/path_utils.py`
Functions:
- `sanitize_remote_path(path: str) -> str`:
  - Strips leading/trailing whitespace.
  - Replaces all backslashes `\` with forward slashes `/`.
  - Strips Windows drive letters if present (e.g. `C:/Users/...` -> `/Users/...`).
  - Normalizes multiple consecutive slashes (e.g. `//` -> `/`).
  - Defaults empty path to `/`.
- `format_local_save_dir(base_dir: str, plc_name: str, sub_dir: str = "", separate_by_date: bool = True) -> Path`:
  - Returns `Path(base_dir) / plc_name / sub_dir / DD-MM-YYYY` (or without date if disabled).
  - Automatically creates parent directories using `.mkdir(parents=True, exist_ok=True)`.

### 4.2 `core/ftp_service.py`
Classes & Functions:
- `list_remote_directories(host, port, username, password, current_dir="/", timeout=10) -> (bool, list[str] | str)`:
  - Connects to FTP and retrieves directory names in `current_dir` (filters out files, returns subfolders and `..` if not at root).
- `FTPDownloader`:
  - Constructor accepts sanitized directories, target folder, file extensions, separate by date, callbacks.
  - `connect(log_callback)` with 10s timeout, capturing debug info on failure.
  - `download_files(progress_callback, log_callback)`:
    - Lists files in each remote directory matching target extensions.
    - Compares file sizes for incremental download (skips if identical local file exists).
    - Maps directory index to sub-folder (`MC1 Connector Leak`, `MC2 Final And Resistance`, `MC3 Auto Appearance`, or `MC{index}`).
    - Downloads via `retrbinary` with thread cancellation support (`is_running`).
  - `stop()`: Signals running thread to stop downloading immediately.

### 4.3 `core/config_service.py`
- `ConfigManager`:
  - Manages reading/writing `config.json`.
  - Ensures default configuration with fallback.
  - Provides thread-safe access to global settings and PLC items (`add_plc`, `update_plc`, `delete_plc`).

### 4.4 `core/logger.py`
- `AppLogger`:
  - Maintains rotating log file handler (`logs/app.log`, max 5MB, 3 backups).
  - Maintains list of registered UI callbacks.
  - Provides helper methods `info()`, `success()`, `warning()`, `error()`.

### 4.5 `ui/components/ftp_browser_dialog.py`
- Modal dialog (`ctk.CTkToplevel`) launched from Add/Edit PLC Dialog:
  - Takes host, port, username, password.
  - Shows current remote path in an editable address bar with a "Go" button and a "Up / Parent Directory" button.
  - Displays a scrollable list of folders found in the current directory.
  - User can double-click a folder to navigate into it.
  - Includes a "Select Current Folder" button that fills the selected path back into the Add/Edit PLC dialog.

### 4.6 `ui/views/`
- `dashboard_view.py`:
  - Manages the scrollable list of PLC cards.
  - Handles per-PLC download triggers and "Download All".
  - Manages connection testing (`🔌`).
  - Manages the Cooldown Timer label for scheduled auto-pull.
- `plc_manager_view.py`:
  - Displays configured PLCs in a responsive table.
  - Add/Edit modal dialog with fields for Name, Host, Port, Username, Password, Remote Dirs, and the "📁 Browse FTP..." button.
- `settings_view.py`:
  - UI for setting local destination folder, file extensions, date grouping checkbox, and auto-pull interval minutes.

### 4.7 `ui/app.py`
- Main application window (`ctk.CTk`).
- Left sidebar navigation buttons (Overview, PLC Manager, Settings).
- Frame switching logic (`select_frame_by_name`).
- Background auto-pull timer scheduling via Tkinter `after()`.

---

## 5. Error Handling & Edge Cases

| Scenario | Handling |
|---|---|
| User types `C:\Users\user\...` in remote directory | `sanitize_remote_path()` removes `C:` and converts `\` to `/`, yielding `/Users/user/...`. |
| Network timeout during FTP connection | `timeout=10` prevents GUI freeze; error message logged in red on UI console. |
| User clicks Browse FTP with empty/invalid host | Validation popup alerts user to enter Host and Port first. |
| Auto-pull fires while manual download is running | Active download lock prevents overlapping downloads on the same PLC. |
| Missing `config.json` | Recreated with valid defaults automatically. |

---

## 6. Verification Plan

1. **Path Sanitizer Unit Tests:** Run test cases covering Windows drive letters, backslashes, multiple slashes, and relative paths.
2. **FTP Service Integration Test:** Test connection, directory listing, and downloading using Python test script against the active local FTP server (`192.168.1.169`).
3. **UI Verification:** Launch `main.py`, verify navigation between Overview, PLC Manager, and Settings.
4. **FTP Browser Dialog Verification:** Open Add/Edit PLC, click "📁 Browse FTP...", navigate into `Documents/Projects/data_record/TEST/Data-TEST`, and verify directory is populated.
5. **Build Verification:** Run `build_quick.bat` or verify Nuitka command syntax to ensure `FTP_Control.exe` can still be packaged with the new directory structure.

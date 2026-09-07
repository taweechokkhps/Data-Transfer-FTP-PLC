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

                    # Incremental check: if file exists and remote size is identical, skip
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

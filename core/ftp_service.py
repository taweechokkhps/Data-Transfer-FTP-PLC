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
    def __init__(self, host, port, username, password, machines, local_target_dir, file_extensions, separate_by_date, plc_name):
        self.host = host
        self.port = int(port)
        self.username = username
        self.password = password

        # Support both machine list of dicts [{'name': '...', 'remote_dir': '...'}] and legacy remote_dirs list of str
        self.machines = []
        if machines and isinstance(machines[0], dict):
            for m in machines:
                m_name = m.get("name", "").strip() or "Machine"
                m_dir = sanitize_remote_path(m.get("remote_dir", "/"))
                self.machines.append({"name": m_name, "remote_dir": m_dir})
        elif machines and isinstance(machines[0], str):
            for idx, d in enumerate(machines):
                self.machines.append({"name": f"MC{idx + 1}", "remote_dir": sanitize_remote_path(d)})
        else:
            self.machines.append({"name": "MC1", "remote_dir": "/"})

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

    def _try_cwd(self, ftp, path: str) -> tuple[bool, str]:
        import re
        candidates = [path]
        stripped = re.sub(r'^/Users/[^/]+', '', path)
        if stripped and stripped != path:
            candidates.append(stripped)
        
        for cand in candidates:
            try:
                ftp.cwd(cand)
                return True, cand
            except Exception:
                pass
        try:
            ftp.cwd(path)
            return True, path
        except Exception as e:
            return False, str(e)

    def download_files(self, progress_callback=None, log_callback=None) -> bool:
        self.is_running = True
        success, msg = self.connect(log_callback)
        if not success:
            if log_callback:
                log_callback(f"[{self.plc_name}] {msg}")
            self.is_running = False
            return False

        try:
            files_by_machine = {}
            total_target_files = []
            for m in self.machines:
                if not self.is_running:
                    break
                r_dir = m["remote_dir"]
                ok, actual_dir = self._try_cwd(self.ftp, r_dir)
                if not ok:
                    if log_callback:
                        log_callback(f"[{self.plc_name}] Error accessing {m['name']} ({r_dir}): {actual_dir}")
                    continue
                try:
                    files = self.ftp.nlst()
                    t_files = [f for f in files if any(f.lower().endswith(ext) for ext in self.file_extensions)]
                    files_by_machine[m["name"]] = (actual_dir, t_files)
                    total_target_files.extend(t_files)
                except Exception as e:
                    if log_callback:
                        log_callback(f"[{self.plc_name}] Error listing {m['name']} ({actual_dir}): {e}")

            if not total_target_files:
                if log_callback:
                    log_callback(f"[{self.plc_name}] No matching files found in any machine directory.")
                self.disconnect()
                self.is_running = False
                return True

            total_files = len(total_target_files)
            current_index = 0

            for m_name, (r_dir, t_files) in files_by_machine.items():
                if not self.is_running:
                    break
                save_dir = format_local_save_dir(self.local_target_dir, self.plc_name, m_name, self.separate_by_date)

                ok, _ = self._try_cwd(self.ftp, r_dir)
                if not ok:
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
                                log_callback(f"[{self.plc_name}][{m_name}] Downloading {pure_filename}...")
                            self.ftp.retrbinary(f"RETR {filename}", f.write)
                        current_index += 1
                        if progress_callback:
                            progress_callback(current_index, total_files)
                    except Exception as e:
                        if log_callback:
                            log_callback(f"[{self.plc_name}][{m_name}] Error downloading {filename}: {e}")

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

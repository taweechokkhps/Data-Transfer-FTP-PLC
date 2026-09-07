import ftplib
import os
import io
import time
import datetime
from pathlib import Path
from contextlib import redirect_stdout
from core.path_utils import sanitize_remote_path, format_local_save_dir, parse_date_from_filename, format_batch_save_dir
from core.logger import logger

def test_connection(host: str, port: int, username: str, password: str, timeout: int = 5, ftp_mode: str = "auto") -> tuple[bool, str]:
    """Test FTP connection and login."""
    try:
        ftp = ftplib.FTP()
        ftp.connect(host, int(port), timeout=timeout)
        ftp.login(username, password)
        if ftp_mode == "active":
            ftp.set_pasv(False)
        ftp.quit()
        return True, "Connected successfully."
    except Exception as e:
        if '530' in str(e):
            return False, "530 Not logged in (Username or Password incorrect)."
        return False, str(e)

def list_remote_directories(host: str, port: int, username: str, password: str, current_dir: str = "/", timeout: int = 10, ftp_mode: str = "auto") -> tuple[bool, list[str] | str]:
    """List subdirectories in current_dir on remote FTP server."""
    clean_dir = sanitize_remote_path(current_dir)
    try:
        ftp = ftplib.FTP()
        ftp.connect(host, int(port), timeout=timeout)
        ftp.login(username, password)
        if ftp_mode == "active":
            ftp.set_pasv(False)
        
        # Try clean_dir and candidate fallbacks
        candidates = [clean_dir]
        stripped = re.sub(r'^[/\\]Users[/\\][^/\\]+', '', clean_dir, flags=re.IGNORECASE)
        if stripped and stripped != clean_dir:
            candidates.insert(0, stripped)
        cwd_ok = False
        for c in candidates:
            try:
                ftp.cwd(c)
                clean_dir = c
                cwd_ok = True
                break
            except Exception:
                pass
        if not cwd_ok:
            ftp.cwd(clean_dir)
        
        dir_names = []
        lines = []
        try:
            ftp.dir(lines.append)
        except Exception as e:
            if "502" in str(e) or "PASV" in str(e).upper():
                ftp.set_pasv(False)
                lines.clear()
                ftp.dir(lines.append)
            else:
                raise
        
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
                try:
                    nlst_items = ftp.nlst()
                except Exception as e:
                    if "502" in str(e) or "PASV" in str(e).upper():
                        ftp.set_pasv(False)
                        nlst_items = ftp.nlst()
                    else:
                        raise

                for item in nlst_items:
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
    def __init__(self, host, port, username, password, machines, local_target_dir, file_extensions, separate_by_date, plc_name, date_filter=None, ftp_mode="auto"):
        self.host = host
        self.port = int(port)
        self.username = username
        self.password = password
        self.date_filter = date_filter or {"mode": "all"}
        self.ftp_mode = (ftp_mode or "auto").lower()
        self.is_active_mode = (self.ftp_mode == "active")

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
                if self.is_active_mode or self.ftp_mode == "active":
                    self.ftp.set_pasv(False)
            self.ftp.set_debuglevel(0)
            return True, "Connected successfully."
        except Exception as e:
            debug_log = debug_output.getvalue()
            if log_callback and debug_log:
                log_callback(f"[{self.plc_name}] --- FTP Debug Log Start ---\n{debug_log}[{self.plc_name}] --- FTP Debug Log End ---")
            if '530' in str(e):
                return False, f"Connection failed: 530 Not logged in. (Username or Password incorrect)"
            return False, f"Connection failed: {e}"

    def _safe_nlst(self, log_callback=None) -> list[str]:
        """Runs nlst with automatic fallback to Active (PORT) mode on 502 error."""
        try:
            return self.ftp.nlst()
        except Exception as e:
            err_str = str(e)
            if "502" in err_str or "PASV" in err_str.upper():
                if log_callback:
                    log_callback(f"[{self.plc_name}] Notice: 502 PASV not implemented by PLC. Automatically switching to Active (PORT) mode.")
                logger.info(f"[{self.plc_name}] Switching to Active (PORT) mode due to 502 PASV error.")
                self.ftp.set_pasv(False)
                self.is_active_mode = True
                return self.ftp.nlst()
            raise

    def _safe_retrbinary(self, cmd: str, callback, log_callback=None):
        """Runs retrbinary with automatic fallback to Active (PORT) mode on 502 error."""
        try:
            return self.ftp.retrbinary(cmd, callback)
        except Exception as e:
            err_str = str(e)
            if "502" in err_str or "PASV" in err_str.upper():
                if log_callback:
                    log_callback(f"[{self.plc_name}] Notice: 502 PASV not implemented by PLC. Automatically switching to Active (PORT) mode.")
                logger.info(f"[{self.plc_name}] Switching to Active (PORT) mode due to 502 PASV error.")
                self.ftp.set_pasv(False)
                self.is_active_mode = True
                return self.ftp.retrbinary(cmd, callback)
            raise

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
        candidates = []
        stripped = re.sub(r'^[/\\]Users[/\\][^/\\]+', '', path, flags=re.IGNORECASE)
        if stripped and stripped != path:
            candidates.append(stripped)
        candidates.append(path)
        
        # Add relative versions (without leading slash)
        for c in list(candidates):
            rel = c.lstrip('/')
            if rel and rel not in candidates:
                candidates.append(rel)
        
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
        start_time = time.time()
        self.is_running = True
        success, msg = self.connect(log_callback)
        if not success:
            if log_callback:
                log_callback(f"[{self.plc_name}] {msg}")
            self.is_running = False
            return False

        try:
            mode = self.date_filter.get("mode", "all")
            start_str = self.date_filter.get("start_date", "").strip()
            end_str = self.date_filter.get("end_date", "").strip()

            start_date = None
            end_date = None
            if mode == "range" and start_str and end_str:
                try:
                    start_date = datetime.datetime.strptime(start_str, "%d/%m/%Y").date()
                    end_date = datetime.datetime.strptime(end_str, "%d/%m/%Y").date()
                    if start_date > end_date:
                        start_date, end_date = end_date, start_date
                except Exception as e:
                    if log_callback:
                        log_callback(f"[{self.plc_name}] Invalid date format ({start_str} - {end_str}): {e}")

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
                    files = self._safe_nlst(log_callback=log_callback)
                    candidate_files = [f for f in files if any(f.lower().endswith(ext) for ext in self.file_extensions)]
                    
                    t_files = []
                    file_dates = []
                    for f in candidate_files:
                        f_date = parse_date_from_filename(f)
                        if f_date:
                            file_dates.append(f_date)
                        if mode == "range" and start_date and end_date:
                            if f_date and start_date <= f_date <= end_date:
                                t_files.append(f)
                        else:
                            t_files.append(f)

                    # Determine batch folder name
                    if mode == "range" and start_date and end_date:
                        batch_folder_name = f"({start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')})"
                    elif file_dates:
                        min_d = min(file_dates)
                        max_d = max(file_dates)
                        batch_folder_name = f"({min_d.strftime('%d-%m-%Y')} - {max_d.strftime('%d-%m-%Y')}) ALL"
                    else:
                        batch_folder_name = "(ALL_FILES)"

                    files_by_machine[m["name"]] = (actual_dir, t_files, batch_folder_name)
                    total_target_files.extend(t_files)
                except Exception as e:
                    if log_callback:
                        log_callback(f"[{self.plc_name}] Error listing {m['name']} ({actual_dir}): {e}")

            if not total_target_files:
                if log_callback:
                    if mode == "range" and start_date and end_date:
                        log_callback(f"[{self.plc_name}] No matching files found in date range {start_str} - {end_str}.")
                    else:
                        log_callback(f"[{self.plc_name}] No matching files found in any machine directory.")
                self.disconnect()
                self.is_running = False
                return True

            total_files = len(total_target_files)
            current_index = 0

            for m_name, (r_dir, t_files, batch_folder_name) in files_by_machine.items():
                if not self.is_running:
                    break
                save_dir = format_batch_save_dir(self.local_target_dir, self.plc_name, m_name, batch_folder_name)

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
                            self._safe_retrbinary(f"RETR {filename}", f.write, log_callback=log_callback)
                        current_index += 1
                        if progress_callback:
                            progress_callback(current_index, total_files)
                    except Exception as e:
                        if log_callback:
                            log_callback(f"[{self.plc_name}][{m_name}] Error downloading {filename}: {e}")

            elapsed = time.time() - start_time
            mins, secs = divmod(int(elapsed), 60)
            dur_str = f"{mins:02d}:{secs:02d}" if mins > 0 else f"{elapsed:.1f}s"
            if log_callback:
                log_callback(f"[{self.plc_name}] Download process completed in {dur_str} ({current_index}/{total_files} files).")
        except Exception as e:
            if log_callback:
                log_callback(f"[{self.plc_name}] FTP Error: {e}")
        finally:
            self.disconnect()
            self.is_running = False

        return True

    def stop(self):
        self.is_running = False

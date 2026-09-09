import ftplib
import socket
import os
import io
import time
import datetime
import re
from pathlib import Path
from contextlib import redirect_stdout
from core.path_utils import sanitize_remote_path, format_local_save_dir, parse_date_from_filename, format_batch_save_dir, get_batch_subdirs
from core.converter_service import convert_txt_to_csv
from core.logger import logger

def test_connection(host: str, port: int, username: str, password: str, timeout: int = 15, ftp_mode: str = "auto") -> tuple[bool, str]:
    """Test FTP connection and login."""
    ftp = ftplib.FTP()
    try:
        ftp.connect(host, int(port), timeout=timeout)
        ftp.login(username, password)
        mode = (ftp_mode or "auto").lower()
        if mode == "active":
            ftp.set_pasv(False)
        else:
            try:
                ftp.sendcmd('OPTS UTF8 ON')
            except Exception:
                pass
        ftp.quit()
        return True, "Connected successfully."
    except Exception as e:
        try:
            ftp.close()
        except Exception:
            pass
        if '530' in str(e):
            return False, "530 Not logged in (Username or Password incorrect)."
        return False, str(e)

def list_remote_items(host: str, port: int, username: str, password: str, current_dir: str = "/", timeout: int = 30, ftp_mode: str = "auto") -> tuple[bool, dict | str]:
    """
    List both subdirectories and files in current_dir on remote FTP server.
    Returns (True, {"folders": [...], "files": [{"name": ..., "size": ...}], "current_dir": clean_dir}) or (False, error_msg).
    Supports MLSD (RFC 3659), LIST (DOS/Unix), NLST, UTF-8/CP874 negotiation, and auto-fallback between Passive/Active modes.
    """
    clean_dir = sanitize_remote_path(current_dir)
    try:
        ftp = ftplib.FTP()
        ftp.connect(host, int(port), timeout=timeout)
        ftp.login(username, password)
        
        mode = (ftp_mode or "auto").lower()
        if mode == "active":
            ftp.set_pasv(False)
        else:
            # Enable UTF-8 if supported by server (RFC 2640 / Windows IIS)
            try:
                ftp.sendcmd('OPTS UTF8 ON')
            except Exception:
                pass

        # Try clean_dir and candidate fallbacks
        candidates = [clean_dir]
        stripped = re.sub(r'^[/\\]Users[/\\][^/\\]+', '', clean_dir, flags=re.IGNORECASE)
        if stripped and stripped not in candidates:
            candidates.append(stripped)
        
        rel = clean_dir.lstrip('/')
        if rel and rel not in candidates:
            candidates.append(rel)
        if stripped:
            rel_str = stripped.lstrip('/')
            if rel_str and rel_str not in candidates:
                candidates.append(rel_str)

        cwd_ok = False
        last_cwd_err = None
        for c in candidates:
            for enc in [ftp.encoding, 'cp874', 'tis-620', 'latin-1']:
                try:
                    ftp.encoding = enc
                    ftp.cwd(c)
                    clean_dir = c
                    cwd_ok = True
                    break
                except Exception as e:
                    last_cwd_err = e
            if cwd_ok:
                break

        if not cwd_ok:
            try:
                ftp.quit()
            except Exception:
                pass
            return False, f"Cannot open directory '{clean_dir}': {last_cwd_err}"

        folders = []
        files = []

        # Strategy 1: MLSD (RFC 3659 standard - clean metadata if supported)
        mlsd_worked = False
        try:
            for name, facts in ftp.mlsd():
                if name in [".", ".."]:
                    continue
                ftype = facts.get("type", "").lower()
                if ftype in ["dir", "pdir", "cdir"]:
                    if ftype == "dir":
                        folders.append(name)
                else:
                    sz = int(facts.get("size", 0))
                    files.append({"name": name, "size": sz})
            mlsd_worked = True
        except Exception:
            folders.clear()
            files.clear()

        # Strategy 2: ftp.dir (standard LIST with DOS / Unix parsing)
        if not mlsd_worked:
            lines = []
            def _fetch_dir():
                try:
                    ftp.dir(lines.append)
                except UnicodeError:
                    for fb_enc in ['cp874', 'latin-1', 'tis-620']:
                        try:
                            ftp.encoding = fb_enc
                            lines.clear()
                            ftp.dir(lines.append)
                            return
                        except Exception:
                            pass
                    raise
                except Exception as e:
                    if "502" in str(e) or "PASV" in str(e).upper() or "TIMEOUT" in str(e).upper():
                        ftp.set_pasv(False)
                        lines.clear()
                        try:
                            ftp.dir(lines.append)
                        except UnicodeError:
                            for fb_enc in ['cp874', 'latin-1', 'tis-620']:
                                try:
                                    ftp.encoding = fb_enc
                                    lines.clear()
                                    ftp.dir(lines.append)
                                    return
                                except Exception:
                                    pass
                            raise
                    else:
                        raise

            try:
                _fetch_dir()
            except Exception as e:
                try:
                    ftp.quit()
                except Exception:
                    pass
                return False, f"Failed to list directory contents: {e}"

            for line in lines:
                parts = line.split()
                if not parts:
                    continue
                # DOS format: "05-14-25  10:00AM       <DIR>          MEMCARD"
                # or:         "05-14-25  10:00AM               14520  DATA01.TXT"
                if "<DIR>" in parts:
                    dir_idx = parts.index("<DIR>")
                    name = " ".join(parts[dir_idx + 1:])
                    if name not in [".", ".."]:
                        folders.append(name)
                elif len(parts) >= 4 and parts[2].isdigit():
                    size = int(parts[2])
                    name = " ".join(parts[3:])
                    if name not in [".", ".."]:
                        files.append({"name": name, "size": size})
                # Unix format: "drwxr-xr-x ..." or "-rw-r--r-- ..."
                elif parts[0].startswith('d'):
                    name = " ".join(parts[8:])
                    if name not in [".", ".."]:
                        folders.append(name)
                elif parts[0].startswith('-'):
                    name = " ".join(parts[8:])
                    size = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
                    if name not in [".", ".."]:
                        files.append({"name": name, "size": size})

        # Strategy 3: Fallback via nlst() if nothing was detected
        if not folders and not files:
            try:
                nlst_items = []
                try:
                    nlst_items = ftp.nlst()
                except Exception as e:
                    if "502" in str(e) or "PASV" in str(e).upper():
                        ftp.set_pasv(False)
                        nlst_items = ftp.nlst()
                for item in nlst_items:
                    if item in [".", ".."]:
                        continue
                    try:
                        ftp.cwd(f"{clean_dir.rstrip('/')}/{item}")
                        folders.append(item)
                        ftp.cwd(clean_dir)
                    except Exception:
                        files.append({"name": item, "size": 0})
            except Exception:
                pass

        try:
            ftp.quit()
        except Exception:
            pass

        return True, {
            "current_dir": clean_dir,
            "folders": sorted(folders, key=str.lower),
            "files": sorted(files, key=lambda x: x["name"].lower())
        }
    except Exception as e:
        return False, f"Failed to list directory: {e}"

def list_remote_directories(host: str, port: int, username: str, password: str, current_dir: str = "/", timeout: int = 10, ftp_mode: str = "auto") -> tuple[bool, list[str] | str]:
    """Legacy helper returning only directory names for backward compatibility."""
    ok, data = list_remote_items(host, port, username, password, current_dir, timeout=timeout, ftp_mode=ftp_mode)
    if ok:
        return True, data.get("folders", [])
    return False, data

def _emit_log(callback, message: str, level: str = "info"):
    if not callback:
        return
    try:
        callback(message, level)
    except TypeError:
        callback(message)

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
                self.ftp.connect(self.host, self.port, timeout=60)
                self.ftp.login(self.username, self.password)
                if self.is_active_mode or self.ftp_mode == "active":
                    self.ftp.set_pasv(False)
                else:
                    try:
                        self.ftp.sendcmd('OPTS UTF8 ON')
                    except Exception:
                        pass
                if hasattr(self.ftp, 'sock') and self.ftp.sock:
                    self.ftp.sock.settimeout(60.0)
            self.ftp.set_debuglevel(0)
            return True, "Connected successfully."
        except Exception as e:
            self.disconnect()
            debug_log = debug_output.getvalue()
            if log_callback and debug_log:
                _emit_log(log_callback, f"[{self.plc_name}] --- FTP Debug Log Start ---\n{debug_log}[{self.plc_name}] --- FTP Debug Log End ---", "warning")
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
                _emit_log(log_callback, f"[{self.plc_name}] Notice: 502 PASV not implemented by PLC. Automatically switching to Active (PORT) mode.", "switch_mode")
                logger.switch_mode(f"[{self.plc_name}] Switching to Active (PORT) mode due to 502 PASV error.")
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
                _emit_log(log_callback, f"[{self.plc_name}] Notice: 502 PASV not implemented by PLC. Automatically switching to Active (PORT) mode.", "switch_mode")
                logger.switch_mode(f"[{self.plc_name}] Switching to Active (PORT) mode due to 502 PASV error.")
                self.ftp.set_pasv(False)
                self.is_active_mode = True
                return self.ftp.retrbinary(cmd, callback)
            raise

    def disconnect(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except Exception:
                pass
            try:
                if hasattr(self.ftp, 'sock') and self.ftp.sock:
                    self.ftp.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                if hasattr(self.ftp, 'sock') and self.ftp.sock:
                    self.ftp.sock.close()
            except Exception:
                pass
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
            for enc in [ftp.encoding, 'cp874', 'tis-620', 'latin-1']:
                try:
                    ftp.encoding = enc
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
            _emit_log(log_callback, f"[{self.plc_name}] {msg}", "error")
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
                    _emit_log(log_callback, f"[{self.plc_name}] Invalid date format ({start_str} - {end_str}): {e}", "warning")

            error_count = 0
            files_by_machine = {}
            total_target_files = []
            for m in self.machines:
                if not self.is_running:
                    break
                r_dir = m["remote_dir"]
                ok, actual_dir = self._try_cwd(self.ftp, r_dir)
                if not ok:
                    _emit_log(log_callback, f"[{self.plc_name}] ❌ Error accessing {m['name']} ({r_dir}): {actual_dir}", "error")
                    error_count += 1
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
                    _emit_log(log_callback, f"[{self.plc_name}] ❌ Error listing {m['name']} ({actual_dir}): {e}", "error")
                    error_count += 1

            if not total_target_files:
                if mode == "range" and start_date and end_date:
                    _emit_log(log_callback, f"[{self.plc_name}] No matching files found in date range {start_str} - {end_str}.", "warning")
                else:
                    _emit_log(log_callback, f"[{self.plc_name}] No matching files found in any machine directory.", "warning")
                self.disconnect()
                self.is_running = False
                return True

            total_files = len(total_target_files)
            current_index = 0

            for m_name, (r_dir, t_files, batch_folder_name) in files_by_machine.items():
                if not self.is_running:
                    break
                save_dir = format_batch_save_dir(self.local_target_dir, self.plc_name, m_name, batch_folder_name)
                plaintext_dir, csv_dir = get_batch_subdirs(save_dir)

                ok, _ = self._try_cwd(self.ftp, r_dir)
                if not ok:
                    continue

                # High-Performance Smart Check (Partition into skipped vs to_download)
                today = datetime.date.today()
                skipped_files = []
                to_download = []

                for filename in t_files:
                    if not self.is_running:
                        break
                    pure_filename = Path(filename).name
                    local_filepath = plaintext_dir / pure_filename
                    csv_filename = f"{Path(pure_filename).stem}.csv"
                    csv_filepath = csv_dir / csv_filename

                    is_duplicate = False
                    if local_filepath.exists() and csv_filepath.exists():
                        f_date = parse_date_from_filename(pure_filename)
                        if f_date and f_date < today:
                            # Past file: Already complete and closed, PLC never writes to it again -> instant skip
                            is_duplicate = True
                        else:
                            # Today's file (f_date == today) or active file:
                            # The machine is actively running today! Production data is continuously appended.
                            # We MUST NOT skip today's file, so afternoon/evening records are always updated.
                            is_duplicate = False

                    if is_duplicate:
                        skipped_files.append((filename, pure_filename, local_filepath, csv_filepath))
                    else:
                        to_download.append((filename, pure_filename, local_filepath, csv_filepath))

                if not self.is_running:
                    _emit_log(log_callback, f"[{self.plc_name}] Download stopped by user.", "warning")
                    break

                # Emit duplicate file summary log
                if skipped_files:
                    if not to_download:
                        _emit_log(log_callback, f"[{self.plc_name}][{m_name}] ไฟล์ทั้งหมดมีอยู่แล้วในเครื่อง (ซ้ำ {len(skipped_files)} ไฟล์ - ข้ามการดาวน์โหลด)", "info")
                    else:
                        _emit_log(log_callback, f"[{self.plc_name}][{m_name}] ตรวจพบไฟล์ซ้ำ {len(skipped_files)} ไฟล์ (ข้ามการดาวน์โหลด)", "info")
                    current_index += len(skipped_files)
                    if progress_callback:
                        progress_callback(current_index, total_files)

                # Process downloads for new/updated files
                for filename, pure_filename, local_filepath, csv_filepath in to_download:
                    if not self.is_running:
                        _emit_log(log_callback, f"[{self.plc_name}] Download stopped by user.", "warning")
                        break

                    _emit_log(log_callback, f"[{self.plc_name}][{m_name}] กำลังดาวน์โหลด: {pure_filename}", "info")

                    max_retries = 2
                    for attempt in range(max_retries):
                        if not self.is_running:
                            break
                        try:
                            f_start = time.perf_counter()
                            with open(local_filepath, 'wb') as f:
                                self._safe_retrbinary(f"RETR {filename}", f.write, log_callback=log_callback)
                            f_dur_ms = (time.perf_counter() - f_start) * 1000
                            f_size_kb = local_filepath.stat().st_size / 1024
                            _emit_log(log_callback, f"[{self.plc_name}][{m_name}] Downloaded {pure_filename} ({f_size_kb:.1f} KB) in {f_dur_ms:.1f} ms", "success")

                            # Auto convert to CSV
                            conv_start = time.perf_counter()
                            ok_conv, conv_err, row_count = convert_txt_to_csv(local_filepath, csv_filepath)
                            conv_ms = (time.perf_counter() - conv_start) * 1000
                            if ok_conv:
                                _emit_log(log_callback, f"[{self.plc_name}][{m_name}] Converted to csv/{csv_filepath.name} ({row_count} rows) in {conv_ms:.1f} ms", "success")
                            else:
                                _emit_log(log_callback, f"[{self.plc_name}][{m_name}] Warning: CSV conversion failed for {pure_filename}: {conv_err}", "warning")

                            current_index += 1
                            if progress_callback:
                                progress_callback(current_index, total_files)

                            # Industrial Safe Pacing Delay (150ms):
                            # Yields CPU and network time slice back to Omron CJ2M so Ladder logic and
                            # HMI Heartbeat (FINS) run uninterrupted without triggering 'PLC NOT RESPONSE'.
                            time.sleep(0.15)
                            break
                        except Exception as e:
                            if attempt < max_retries - 1 and self.is_running:
                                _emit_log(log_callback, f"[{self.plc_name}][{m_name}] PLC กำลังบันทึกข้อมูลอยู่ ({pure_filename}) จะลองใหม่ใน 1.5 วินาที...", "warning")
                                time.sleep(1.5)
                            else:
                                _emit_log(log_callback, f"[{self.plc_name}][{m_name}] ❌ Error downloading {filename}: {e}", "error")
                                error_count += 1

            elapsed = time.time() - start_time
            total_ms = elapsed * 1000
            mins, secs = divmod(int(elapsed), 60)
            if mins > 0:
                dur_str = f"{mins:02d}:{secs:02d} ({total_ms:,.0f} ms)"
            else:
                dur_str = f"{elapsed:.3f}s ({total_ms:,.0f} ms)"

            if error_count > 0:
                _emit_log(
                    log_callback,
                    f"[{self.plc_name}] ❌ Download process completed with {error_count} error(s) in {dur_str} ({current_index}/{total_files} files).",
                    "error"
                )
            else:
                _emit_log(
                    log_callback,
                    f"[{self.plc_name}] ✅ Download process completed in {dur_str} ({current_index}/{total_files} files).",
                    "completed"
                )
        except Exception as e:
            _emit_log(log_callback, f"[{self.plc_name}] ❌ FTP Error: {e}", "error")
        finally:
            self.disconnect()
            self.is_running = False

        return True

    def stop(self):
        self.is_running = False

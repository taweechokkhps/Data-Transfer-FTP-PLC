import ftplib
import os
import datetime
from pathlib import Path

class FTPDownloader:
    def __init__(self, host, port, username, password, remote_dirs, local_target_dir, file_extensions, separate_by_date, plc_name):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.remote_dirs = remote_dirs
        self.local_target_dir = local_target_dir
        self.file_extensions = [ext.lower() for ext in file_extensions]
        self.separate_by_date = separate_by_date
        self.plc_name = plc_name
        self.ftp = None
        self.is_running = False

    def connect(self, log_callback=None):
        import io
        from contextlib import redirect_stdout
        
        debug_output = io.StringIO()
        try:
            self.ftp = ftplib.FTP()
            # Set debug level to 1 to see the commands and responses
            self.ftp.set_debuglevel(1)
            
            with redirect_stdout(debug_output):
                self.ftp.connect(self.host, self.port)
                self.ftp.login(self.username, self.password)
                
            self.ftp.set_debuglevel(0)
            return True, "Connected successfully."
        except Exception as e:
            debug_log = debug_output.getvalue()
            if log_callback and debug_log:
                log_callback(f"[{self.plc_name}] --- FTP Debug Log Start ---\n{debug_log}[{self.plc_name}] --- FTP Debug Log End ---")
                
            if '530' in str(e):
                return False, f"Connection failed: 530 Not logged in. (Username หรือ Password อาจจะผิด หรือ PLC ไม่ให้สิทธิ์)"
            return False, f"Connection failed: {e}"

    def disconnect(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                self.ftp.close()
            self.ftp = None

    def get_save_directory(self, sub_dir=""):
        base_dir = Path(self.local_target_dir)
        if self.separate_by_date:
            date_str = datetime.datetime.now().strftime("%d-%m-%Y")
            # Structure: TargetFolder / PLC_Name / MC1 / 18-08-2026
            if sub_dir:
                save_dir = base_dir / self.plc_name / sub_dir / date_str
            else:
                save_dir = base_dir / self.plc_name / date_str
        else:
            if sub_dir:
                save_dir = base_dir / self.plc_name / sub_dir
            else:
                save_dir = base_dir / self.plc_name
            
        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir

    def download_files(self, progress_callback=None, log_callback=None):
        self.is_running = True
        success, msg = self.connect(log_callback)
        if not success:
            if log_callback: log_callback(f"[{self.plc_name}] {msg}")
            self.is_running = False
            return False

        try:
            total_target_files = []
            files_by_dir = {}
            for r_dir in self.remote_dirs:
                if not self.is_running: break
                r_dir = r_dir.strip()
                if not r_dir: continue
                
                try:
                    self.ftp.cwd(r_dir)
                    files = self.ftp.nlst()
                    t_files = [f for f in files if any(f.lower().endswith(ext) for ext in self.file_extensions)]
                    files_by_dir[r_dir] = t_files
                    total_target_files.extend(t_files)
                except Exception as e:
                    if log_callback: log_callback(f"[{self.plc_name}] Error accessing {r_dir}: {e}")
            
            if not total_target_files:
                if log_callback: log_callback(f"[{self.plc_name}] No matching files found in any directory.")
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
                if not self.is_running: break
                
                sub_dir = mc_names.get(dir_index, f"MC{dir_index}")
                save_dir = self.get_save_directory(sub_dir)
                dir_index += 1
                
                try:
                    self.ftp.cwd(r_dir)
                except:
                    continue
                    
                for filename in t_files:
                    if not self.is_running:
                        if log_callback: log_callback(f"[{self.plc_name}] Download stopped by user.")
                        break
                        
                    # Extract only the file name
                    pure_filename = Path(filename).name
                    local_filepath = save_dir / pure_filename
                    
                    try:
                        with open(local_filepath, 'wb') as f:
                            if log_callback: log_callback(f"[{self.plc_name}] Downloading {r_dir}/{pure_filename}...")
                            self.ftp.retrbinary(f"RETR {filename}", f.write)
                        
                        current_index += 1
                        if progress_callback:
                            progress_callback(current_index, total_files)
                    except Exception as e:
                        if log_callback: log_callback(f"[{self.plc_name}] Error downloading {filename}: {e}")
                    
            if log_callback: log_callback(f"[{self.plc_name}] Download process completed.")
            
        except Exception as e:
            if log_callback: log_callback(f"[{self.plc_name}] FTP Error: {e}")
        finally:
            self.disconnect()
            self.is_running = False
            
        return True

    def stop(self):
        self.is_running = False

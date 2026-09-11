from typing import Dict, Any, Tuple, Optional, List
from core.logger import logger
from core.path_utils import sanitize_remote_path
from core.ftp_service import test_connection as ftp_test_connection
from ui.components.date_picker import validate_date_range

class PLCManagerController:
    """Controller handling CRUD operations, validation, and connectivity tests for PLCs."""

    def __init__(self, config_manager, app_logger=None):
        self.config_manager = config_manager
        self.logger = app_logger or logger

    def get_plcs(self) -> List[Dict[str, Any]]:
        """Return the current list of PLC configurations."""
        return self.config_manager.get().get("plcs", [])

    def validate_plc(self, data: Dict[str, Any], edit_index: Optional[int] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate and sanitize PLC configuration data, ensuring no duplicate IP or Name.
        Returns (is_valid: bool, message: str, sanitized_data: Optional[Dict]).
        """
        line_name = str(data.get("name", "")).strip()
        if not line_name:
            return False, "Line / PLC Name cannot be empty.", None

        host = str(data.get("host", "")).strip()
        if not host:
            return False, "Host / IP Address cannot be empty.", None

        raw_port = data.get("port", 21)
        try:
            port = int(raw_port)
            if port < 1 or port > 65535:
                port = 21
        except (ValueError, TypeError):
            port = 21

        # Check for duplicate name or IP:port against other PLCs
        existing_plcs = self.get_plcs()
        for idx, existing in enumerate(existing_plcs):
            if edit_index is not None and idx == edit_index:
                continue
            ex_name = str(existing.get("name", "")).strip()
            if ex_name.lower() == line_name.lower():
                return False, f"Line Name '{line_name}' is already used by another Line.", None

            ex_host = str(existing.get("host", "")).strip()
            try:
                ex_port = int(existing.get("port", 21))
            except (ValueError, TypeError):
                ex_port = 21
            if ex_host.lower() == host.lower() and ex_port == port:
                return False, f"IP Address '{host}:{port}' is already used by '{ex_name}'. Duplicate IP is not allowed to prevent connection collisions.", None

        username = str(data.get("username", "ftp")).strip()
        password = str(data.get("password", "")).strip()
        ftp_mode = str(data.get("ftp_mode", "auto")).strip().lower()
        if ftp_mode not in ("auto", "active", "passive"):
            ftp_mode = "auto"

        # Sanitize machines list
        machines_raw = data.get("machines", [])
        sanitized_machines = []
        for m in machines_raw:
            m_name = str(m.get("name", "")).strip()
            m_dir = str(m.get("remote_dir", "")).strip()
            if m_name and m_dir:
                sanitized_machines.append({
                    "name": m_name,
                    "remote_dir": sanitize_remote_path(m_dir)
                })

        if not sanitized_machines:
            sanitized_machines = [{"name": "MC1", "remote_dir": "/"}]

        # Date filter validation
        date_filter = data.get("date_filter", {})
        df_mode = str(date_filter.get("mode", "all")).lower()
        s_date = str(date_filter.get("start_date", "")).strip()
        e_date = str(date_filter.get("end_date", "")).strip()

        if df_mode == "range":
            ok, err_msg, _, _ = validate_date_range(s_date, e_date)
            if not ok:
                return False, err_msg, None
        else:
            df_mode = "all"

        sanitized_data = {
            "name": line_name,
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "ftp_mode": ftp_mode,
            "machines": sanitized_machines,
            "date_filter": {
                "mode": df_mode,
                "start_date": s_date,
                "end_date": e_date
            }
        }
        return True, "Validation successful", sanitized_data

    def add_plc(self, plc_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate and add a new PLC."""
        ok, msg, sanitized = self.validate_plc(plc_data, edit_index=None)
        if not ok:
            return False, msg

        self.config_manager.add_plc(sanitized)
        self.logger.info(f"PLC '{sanitized['name']}' added successfully.")
        return True, "PLC added successfully"

    def update_plc(self, index: int, plc_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate and update an existing PLC."""
        ok, msg, sanitized = self.validate_plc(plc_data, edit_index=index)
        if not ok:
            return False, msg

        self.config_manager.update_plc(index, sanitized)
        self.logger.info(f"PLC #{index} '{sanitized['name']}' updated successfully.")
        return True, "PLC updated successfully"

    def delete_plc(self, index: int) -> Tuple[bool, str]:
        """Delete a PLC by its index."""
        try:
            plcs = self.get_plcs()
            if 0 <= index < len(plcs):
                name = plcs[index].get("name", f"index {index}")
                self.config_manager.delete_plc(index)
                self.logger.info(f"PLC #{index} '{name}' deleted.")
                return True, f"PLC '{name}' deleted successfully"
            return False, f"Invalid PLC index: {index}"
        except Exception as e:
            self.logger.error(f"Failed to delete PLC #{index}: {e}")
            return False, str(e)

    def test_connection(self, host: str, port: int = 21, username: str = "ftp",
                        password: str = "", ftp_mode: str = "auto", timeout: int = 5) -> Tuple[bool, str]:
        """Run connectivity test to a PLC FTP server."""
        return ftp_test_connection(host, port, username, password, timeout=timeout, ftp_mode=ftp_mode)

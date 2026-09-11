import os
import sys
import tempfile
import json
import unittest
from unittest.mock import MagicMock, patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.config_service import ConfigManager
import ui.controllers.dashboard_controller

class TestSettingsController(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "test_config.json")
        initial_data = {
            "global_settings": {
                "target_directory": "C:/InitialDir",
                "file_extensions": [".txt", ".csv"],
                "separate_by_date": False,
                "auto_pull_interval_minutes": 60,
                "auto_pull_enabled": True,
                "auto_pull_lines": ["LINE 1"]
            },
            "plcs": [
                {
                    "name": "LINE 1",
                    "host": "192.168.0.10",
                    "port": 21,
                    "username": "user",
                    "password": "pwd",
                    "machines": [{"name": "MC1", "remote_dir": "/log"}]
                }
            ]
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)
        self.config_manager = ConfigManager(self.config_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_settings_success(self):
        from ui.controllers.settings_controller import SettingsController
        controller = SettingsController(self.config_manager)

        data = {
            "target_directory": "D:/NewDir",
            "file_extensions": [".log", ".csv"],
            "auto_pull_enabled": False,
            "auto_pull_interval_minutes": 30,
            "auto_pull_lines": ["LINE 1"]
        }
        ok, msg = controller.save_settings(data)
        self.assertTrue(ok)
        
        saved = self.config_manager.get()["global_settings"]
        self.assertEqual(saved["target_directory"], "D:/NewDir")
        self.assertEqual(saved["file_extensions"], [".log", ".csv"])
        self.assertFalse(saved["auto_pull_enabled"])
        self.assertEqual(saved["auto_pull_interval_minutes"], 30)

    def test_save_settings_default_fallback(self):
        from ui.controllers.settings_controller import SettingsController
        controller = SettingsController(self.config_manager)

        data = {
            "target_directory": "D:/NewDir",
            "file_extensions": [],  # Empty extensions should fallback to default
            "auto_pull_enabled": True,
            "auto_pull_interval_minutes": "invalid",
            "auto_pull_lines": []
        }
        ok, msg = controller.save_settings(data)
        self.assertTrue(ok)
        
        saved = self.config_manager.get()["global_settings"]
        self.assertEqual(saved["file_extensions"], [".txt", ".csv"])
        self.assertEqual(saved["auto_pull_interval_minutes"], 60)

    def test_format_extension(self):
        from ui.controllers.settings_controller import SettingsController
        self.assertEqual(SettingsController.format_extension("log"), ".log")
        self.assertEqual(SettingsController.format_extension(".LOG"), ".log")
        self.assertEqual(SettingsController.format_extension("   .csv  "), ".csv")
        self.assertIsNone(SettingsController.format_extension(""))


class TestPLCManagerController(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "test_config.json")
        initial_data = {
            "global_settings": {
                "target_directory": "C:/InitialDir",
                "file_extensions": [".txt", ".csv"],
                "auto_pull_interval_minutes": 60,
                "auto_pull_enabled": True
            },
            "plcs": [
                {
                    "name": "LINE 1",
                    "host": "192.168.0.10",
                    "port": 21,
                    "username": "user",
                    "password": "pwd",
                    "ftp_mode": "auto",
                    "machines": [{"name": "MC1", "remote_dir": "/log"}]
                }
            ]
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)
        self.config_manager = ConfigManager(self.config_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_validate_plc_valid(self):
        from ui.controllers.plc_manager_controller import PLCManagerController
        controller = PLCManagerController(self.config_manager)

        valid_data = {
            "name": "LINE 2",
            "host": "192.168.1.50",
            "port": "21",
            "username": "admin",
            "password": "pass",
            "ftp_mode": "auto",
            "machines": [{"name": "MC1", "remote_dir": "/0_CARD/"}],
            "date_filter": {"mode": "all", "start_date": "", "end_date": ""}
        }
        ok, msg, sanitized = controller.validate_plc(valid_data)
        self.assertTrue(ok)
        self.assertEqual(sanitized["name"], "LINE 2")
        self.assertEqual(sanitized["port"], 21)
        self.assertEqual(sanitized["machines"][0]["remote_dir"], "/0_CARD")

    def test_validate_plc_missing_name_or_host(self):
        from ui.controllers.plc_manager_controller import PLCManagerController
        controller = PLCManagerController(self.config_manager)

        # Missing name
        ok, msg, _ = controller.validate_plc({"name": "", "host": "192.168.1.1"})
        self.assertFalse(ok)
        self.assertIn("Name", msg)

        # Missing host
        ok, msg, _ = controller.validate_plc({"name": "LINE 1", "host": ""})
        self.assertFalse(ok)
        self.assertIn("Host", msg)

    def test_validate_plc_invalid_date_range(self):
        from ui.controllers.plc_manager_controller import PLCManagerController
        controller = PLCManagerController(self.config_manager)

        data = {
            "name": "LINE 1",
            "host": "192.168.1.1",
            "port": 21,
            "username": "user",
            "password": "pwd",
            "machines": [{"name": "MC1", "remote_dir": "/"}],
            "date_filter": {
                "mode": "range",
                "start_date": "20/05/2026",
                "end_date": "10/05/2026"  # End before start
            }
        }
        ok, msg, _ = controller.validate_plc(data)
        self.assertFalse(ok)

    def test_validate_plc_duplicate_ip(self):
        from ui.controllers.plc_manager_controller import PLCManagerController
        controller = PLCManagerController(self.config_manager)

        # LINE 1 has host "192.168.0.10" and port 21
        dup_ip_data = {
            "name": "NEW LINE",
            "host": "192.168.0.10",
            "port": 21,
            "username": "admin",
            "password": "pwd",
            "machines": [{"name": "MC1", "remote_dir": "/"}]
        }
        ok, msg, _ = controller.validate_plc(dup_ip_data)
        self.assertFalse(ok)
        self.assertIn("192.168.0.10", msg)
        self.assertIn("LINE 1", msg)

    def test_validate_plc_duplicate_name(self):
        from ui.controllers.plc_manager_controller import PLCManagerController
        controller = PLCManagerController(self.config_manager)

        # LINE 1 already exists
        dup_name_data = {
            "name": "LINE 1",
            "host": "192.168.0.99",
            "port": 21,
            "username": "admin",
            "password": "pwd",
            "machines": [{"name": "MC1", "remote_dir": "/"}]
        }
        ok, msg, _ = controller.validate_plc(dup_name_data)
        self.assertFalse(ok)
        self.assertIn("LINE 1", msg)

    def test_validate_plc_edit_self_allowed(self):
        from ui.controllers.plc_manager_controller import PLCManagerController
        controller = PLCManagerController(self.config_manager)

        # Editing LINE 1 (index 0) with its own IP and name is valid
        edit_self = {
            "name": "LINE 1",
            "host": "192.168.0.10",
            "port": 21,
            "username": "admin",
            "password": "pwd",
            "machines": [{"name": "MC1", "remote_dir": "/"}]
        }
        ok, msg, sanitized = controller.validate_plc(edit_self, edit_index=0)
        self.assertTrue(ok)
        self.assertIsNotNone(sanitized)

    def test_crud_plc(self):
        from ui.controllers.plc_manager_controller import PLCManagerController
        controller = PLCManagerController(self.config_manager)

        # Add
        new_plc = {
            "name": "LINE 2",
            "host": "192.168.1.20",
            "port": 21,
            "username": "user",
            "password": "pwd",
            "machines": [{"name": "MC1", "remote_dir": "/log"}]
        }
        ok, msg = controller.add_plc(new_plc)
        self.assertTrue(ok)
        self.assertEqual(len(controller.get_plcs()), 2)

        # Update
        updated_plc = dict(new_plc)
        updated_plc["name"] = "LINE 2 EDITED"
        ok, msg = controller.update_plc(1, updated_plc)
        self.assertTrue(ok)
        self.assertEqual(controller.get_plcs()[1]["name"], "LINE 2 EDITED")

        # Delete
        ok, msg = controller.delete_plc(0)
        self.assertTrue(ok)
        self.assertEqual(len(controller.get_plcs()), 1)
        self.assertEqual(controller.get_plcs()[0]["name"], "LINE 2 EDITED")


class TestDashboardController(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "test_config.json")
        initial_data = {
            "global_settings": {
                "target_directory": self.temp_dir.name,
                "file_extensions": [".txt", ".csv"],
                "separate_by_date": False,
                "auto_pull_interval_minutes": 60,
                "auto_pull_enabled": True,
                "auto_pull_lines": ["LINE 1"]
            },
            "plcs": [
                {
                    "name": "LINE 1",
                    "host": "192.168.0.10",
                    "port": 21,
                    "username": "user",
                    "password": "pwd",
                    "ftp_mode": "auto",
                    "machines": [{"name": "MC1", "remote_dir": "/log"}]
                },
                {
                    "name": "LINE 2",
                    "host": "192.168.0.11",
                    "port": 21,
                    "username": "user",
                    "password": "pwd",
                    "ftp_mode": "auto",
                    "machines": [{"name": "MC1", "remote_dir": "/log"}]
                }
            ]
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)
        self.config_manager = ConfigManager(self.config_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_triggers_and_active_downloads(self):
        from ui.controllers.dashboard_controller import DashboardController
        controller = DashboardController(self.config_manager)

        self.assertFalse(controller.has_active_downloads())
        
        # Register triggers
        trigger1 = MagicMock()
        trigger2 = MagicMock()
        controller.register_download_trigger("LINE 1", trigger1)
        controller.register_download_trigger("LINE 2", trigger2)

        self.assertEqual(len(controller.plc_download_callbacks), 2)
        self.assertIn("LINE 1", controller.plc_download_by_name)

        # Download selected lines
        controller.download_selected_lines(["LINE 1"])
        trigger1.assert_called_once()
        trigger2.assert_not_called()

        # Stop downloads
        mock_dl = MagicMock()
        controller.active_downloaders["LINE 1"] = mock_dl
        self.assertTrue(controller.has_active_downloads())

        controller.stop_all_downloads()
        mock_dl.cancel.assert_called_once()
        self.assertFalse(controller.has_active_downloads())

    @patch("ui.controllers.dashboard_controller.test_connection")
    def test_test_single_connection(self, mock_test):
        import threading
        from ui.controllers.dashboard_controller import DashboardController
        controller = DashboardController(self.config_manager)

        mock_test.return_value = (True, "OK")
        status_updates = []

        event = threading.Event()
        def on_status(status_text, color, msg_text=""):
            status_updates.append((status_text, color, msg_text))
            if "OK" in status_text:
                event.set()

        plc_data = self.config_manager.get()["plcs"][0]
        controller.test_single_connection(plc_data, on_status=on_status)
        event.wait(timeout=2.0)

        mock_test.assert_called_once()
        self.assertTrue(any("OK" in s[0] for s in status_updates))


if __name__ == "__main__":
    unittest.main()

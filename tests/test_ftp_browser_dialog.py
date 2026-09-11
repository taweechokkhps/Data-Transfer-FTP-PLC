import unittest
from unittest.mock import patch, MagicMock
import customtkinter as ctk

class TestFTPBrowserDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def _create_dialog(self, on_select=None):
        from ui.components.ftp_browser_dialog import FTPBrowserDialog
        with patch("ui.components.ftp_browser_dialog.setup_modal_dialog"), \
             patch("ui.components.ftp_browser_dialog.list_remote_items", return_value=(True, {"current_dir": "/", "folders": [], "files": []})):
            dlg = FTPBrowserDialog(
                self.root,
                "127.0.0.1",
                21,
                "user",
                "pass",
                on_select_callback=on_select or MagicMock()
            )
        return dlg

    def test_dialog_loading_state_disables_select_button(self):
        dlg = self._create_dialog()
        try:
            dlg._set_controls_loading_state(True)
            self.assertTrue(dlg.is_loading)
            self.assertEqual(dlg.btn_select.cget("state"), "disabled")
            self.assertIn("Loading", dlg.btn_select.cget("text"))
        finally:
            dlg.destroy()

    def test_dialog_load_success_enables_select_button(self):
        dlg = self._create_dialog()
        try:
            dlg._set_controls_loading_state(True)
            dlg._on_load_success({"current_dir": "/MEMCARD", "folders": ["F1"], "files": []})
            self.assertFalse(dlg.is_loading)
            self.assertEqual(dlg.btn_select.cget("state"), "normal")
            self.assertEqual(dlg.btn_select.cget("text"), "✓ Select This Directory")
        finally:
            dlg.destroy()

    def test_dialog_load_fail_keeps_select_button_disabled(self):
        dlg = self._create_dialog()
        try:
            dlg._set_controls_loading_state(True)
            dlg._on_load_fail("Connection error")
            self.assertFalse(dlg.is_loading)
            self.assertEqual(dlg.btn_select.cget("state"), "disabled")
        finally:
            dlg.destroy()

    def test_dialog_select_current_blocked_while_loading(self):
        callback = MagicMock()
        dlg = self._create_dialog(on_select=callback)
        try:
            dlg.is_loading = True
            dlg.select_current()
            callback.assert_not_called()
        finally:
            dlg.destroy()

    def test_reset_scroll_to_top(self):
        dlg = self._create_dialog()
        try:
            with patch.object(dlg.content_frame._parent_canvas, "yview_moveto") as mock_moveto:
                dlg._reset_scroll_to_top()
                mock_moveto.assert_called_with(0.0)
        finally:
            dlg.destroy()

if __name__ == "__main__":
    unittest.main()

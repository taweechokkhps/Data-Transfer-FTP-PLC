import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.config_service import ConfigManager
from core.logger import AppLogger

def test_config_crud():
    with tempfile.TemporaryDirectory() as td:
        config_file = Path(td) / "test_config.json"
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

if __name__ == "__main__":
    test_config_crud()
    test_logger_callback()
    print("CONFIG AND LOGGER TESTS PASSED!")

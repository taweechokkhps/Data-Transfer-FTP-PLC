"""
Compatibility shim for ftp_client.py - redirects imports to core.ftp_service.
"""
from core.ftp_service import FTPDownloader, test_connection, list_remote_directories

__all__ = ["FTPDownloader", "test_connection", "list_remote_directories"]

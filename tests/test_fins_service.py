import os
import sys
import unittest
import socket
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.fins_service import (
    build_fins_read_bit_frame,
    parse_fins_read_bit_response,
    check_omron_w200_bit
)

class TestFinsService(unittest.TestCase):
    def test_build_fins_read_bit_frame_w200_00(self):
        frame = build_fins_read_bit_frame(node_id=11, area_code=0x31, word=200, bit=0)
        self.assertEqual(len(frame), 18)
        
        # Header (10 bytes)
        self.assertEqual(frame[0], 0x80)  # ICF
        self.assertEqual(frame[1], 0x00)  # RSV
        self.assertEqual(frame[2], 0x02)  # GCT
        self.assertEqual(frame[3], 0x00)  # DNA
        self.assertEqual(frame[4], 11)    # DA1 (node 11)
        self.assertEqual(frame[5], 0x00)  # DA2 (CPU)
        self.assertEqual(frame[6], 0x00)  # SNA
        self.assertEqual(frame[7], 0x00)  # SA1
        self.assertEqual(frame[8], 0x00)  # SA2
        self.assertEqual(frame[9], 0x01)  # SID

        # Command (2 bytes)
        self.assertEqual(frame[10], 0x01) # MR
        self.assertEqual(frame[11], 0x01) # SR

        # Parameters (6 bytes)
        self.assertEqual(frame[12], 0x31) # Area code: WR Bit
        self.assertEqual(frame[13], 0x00) # Word 200 high byte
        self.assertEqual(frame[14], 0xC8) # Word 200 low byte (200 = 0x00C8)
        self.assertEqual(frame[15], 0x00) # Bit 0
        self.assertEqual(frame[16], 0x00) # Count high byte
        self.assertEqual(frame[17], 0x01) # Count low byte (1 bit)

    def test_parse_response_bit_on(self):
        # 10 bytes header + 2 bytes cmd + 2 bytes MRES/SRES (00 00) + 1 byte data (01 = ON)
        resp = bytes([0xC0, 0, 2, 0, 0, 0, 0, 11, 0, 1, 1, 1, 0, 0, 1])
        ok, is_on, msg = parse_fins_read_bit_response(resp)
        self.assertTrue(ok)
        self.assertTrue(is_on)
        self.assertEqual(msg, "OK")

    def test_parse_response_bit_off(self):
        # 10 bytes header + 2 bytes cmd + 2 bytes MRES/SRES (00 00) + 1 byte data (00 = OFF)
        resp = bytes([0xC0, 0, 2, 0, 0, 0, 0, 11, 0, 1, 1, 1, 0, 0, 0])
        ok, is_on, msg = parse_fins_read_bit_response(resp)
        self.assertTrue(ok)
        self.assertFalse(is_on)
        self.assertEqual(msg, "OK")

    def test_parse_response_error_code(self):
        # MRES = 0x11, SRES = 0x01 (Address out of range)
        resp = bytes([0xC0, 0, 2, 0, 0, 0, 0, 11, 0, 1, 1, 1, 0x11, 0x01])
        ok, is_on, msg = parse_fins_read_bit_response(resp)
        self.assertFalse(ok)
        self.assertIsNone(is_on)
        self.assertIn("1101", msg)

    def test_parse_response_too_short(self):
        resp = bytes([0xC0, 0, 2, 0])
        ok, is_on, msg = parse_fins_read_bit_response(resp)
        self.assertFalse(ok)
        self.assertIsNone(is_on)

    @patch('socket.socket')
    def test_check_omron_w200_bit_on(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock
        # Mock response returning bit ON
        mock_sock.recvfrom.return_value = (bytes([0xC0, 0, 2, 0, 0, 0, 0, 11, 0, 1, 1, 1, 0, 0, 1]), ("192.168.0.11", 9600))

        ok, is_on, msg = check_omron_w200_bit("192.168.0.11", port=9600, timeout=1.0)
        self.assertTrue(ok)
        self.assertTrue(is_on)

    @patch('socket.socket')
    def test_check_omron_w200_bit_off(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock
        # Mock response returning bit OFF
        mock_sock.recvfrom.return_value = (bytes([0xC0, 0, 2, 0, 0, 0, 0, 11, 0, 1, 1, 1, 0, 0, 0]), ("192.168.0.11", 9600))

        ok, is_on, msg = check_omron_w200_bit("192.168.0.11", port=9600, timeout=1.0)
        self.assertTrue(ok)
        self.assertFalse(is_on)

    @patch('socket.socket')
    def test_check_omron_w200_bit_timeout(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock
        mock_sock.recvfrom.side_effect = socket.timeout("timed out")

        ok, is_on, msg = check_omron_w200_bit("192.168.0.11", port=9600, timeout=1.0)
        self.assertFalse(ok)
        self.assertIsNone(is_on)
        self.assertIn("Timeout", msg)

if __name__ == "__main__":
    unittest.main()

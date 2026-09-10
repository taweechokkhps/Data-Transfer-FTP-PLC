import socket
import struct

def build_fins_read_bit_frame(node_id: int = 0, area_code: int = 0x31, word: int = 200, bit: int = 0) -> bytes:
    """
    Constructs an 18-byte Omron FINS/UDP frame to read a single bit from memory area.
    Default area_code 0x31 = Work Area Bit (WR).
    Word 200, Bit 0 = W200.00.
    """
    # 10-byte FINS Header
    header = bytes([
        0x80,               # ICF: Command requiring response
        0x00,               # RSV: Reserved
        0x02,               # GCT: Permissible gateway count
        0x00,               # DNA: Destination network (0 = local)
        node_id & 0xFF,     # DA1: Destination node (last octet of PLC IP or 0)
        0x00,               # DA2: Destination unit (0 = CPU)
        0x00,               # SNA: Source network
        0x00,               # SA1: Source node
        0x00,               # SA2: Source unit
        0x01                # SID: Service ID
    ])

    # 2-byte Command (01 01 = Memory Area Read)
    command = bytes([0x01, 0x01])

    # 6-byte Parameters (Area code + 3-byte address + 2-byte count)
    # Address: 2 bytes word (big-endian) + 1 byte bit (0-15)
    # Count: 2 bytes count (big-endian: 1 bit = 0x0001)
    params = struct.pack(">BHBBH", area_code, word, bit & 0x0F, 0x00, 1)

    # Note: struct.pack(">BHBBH") creates:
    # B: area_code (1 byte)
    # H: word (2 bytes)
    # B: bit (1 byte)
    # H: count (2 bytes)
    # Total params = 1 + 2 + 1 + 2 = 6 bytes
    return header + bytes([0x01, 0x01, area_code, (word >> 8) & 0xFF, word & 0xFF, bit & 0xFF, 0x00, 0x01])

def parse_fins_read_bit_response(response: bytes) -> tuple[bool, bool | None, str]:
    """
    Parses a FINS/UDP response frame for Memory Area Read (Bit).
    Returns (success: bool, is_on: bool | None, message: str).
    """
    if not response or len(response) < 14:
        return False, None, "Invalid response: frame too short"

    # Bytes 10-11: Command echo (0x01, 0x01)
    # Bytes 12-13: Main Response Code (MRES) and Sub Response Code (SRES)
    mres = response[12]
    sres = response[13]

    if mres != 0x00 or sres != 0x00:
        error_hex = f"{mres:02X}{sres:02X}"
        return False, None, f"FINS Error Response Code: {error_hex}"

    # Response data starts at byte 14
    if len(response) < 15:
        return False, None, "Invalid response: missing data payload"

    bit_val = response[14]
    is_on = (bit_val == 0x01)
    return True, is_on, "OK"

def check_omron_w200_bit(host: str, port: int = 9600, timeout: float = 2.0) -> tuple[bool, bool | None, str]:
    """
    Checks the status of Omron PLC bit W200.00 via FINS/UDP.
    Returns:
        (success, is_on, message)
        - success=True, is_on=True: Machine is active (W200.00 is ON)
        - success=True, is_on=False: Machine is idle (W200.00 is OFF)
        - success=False: Communication failed (Timeout, network unreachable, etc.)
    """
    try:
        node_id = 0
        try:
            parts = host.strip().split(".")
            if len(parts) == 4:
                node_id = int(parts[3]) & 0xFF
        except Exception:
            node_id = 0

        # Build 18-byte FINS request for W200.00 (Area 0x31, Word 200, Bit 0)
        request = build_fins_read_bit_frame(node_id=node_id, area_code=0x31, word=200, bit=0)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        try:
            sock.sendto(request, (host, port))
            response, _ = sock.recvfrom(1024)
        finally:
            sock.close()

        return parse_fins_read_bit_response(response)
    except socket.timeout:
        return False, None, f"FINS Timeout ({timeout}s) on {host}:{port}"
    except Exception as e:
        return False, None, f"FINS Error: {e}"

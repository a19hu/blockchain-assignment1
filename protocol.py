"""
Simple length-prefixed JSON protocol over TCP.
Message: 4-byte big-endian length + UTF-8 JSON.
"""
import json
import struct


def encode_message(obj: dict) -> bytes:
    payload = json.dumps(obj).encode("utf-8")
    return struct.pack(">I", len(payload)) + payload


def decode_message(data: bytes) -> dict | None:
    if len(data) < 4:
        return None
    (length,) = struct.unpack(">I", data[:4])
    if len(data) < 4 + length:
        return None
    return json.loads(data[4 : 4 + length].decode("utf-8"))


def read_message(sock) -> dict | None:
    """Read one length-prefixed message from socket."""
    header = sock.recv(4)
    if len(header) < 4:
        return None
    (length,) = struct.unpack(">I", header)
    buf = b""
    while len(buf) < length:
        chunk = sock.recv(min(4096, length - len(buf)))
        if not chunk:
            return None
        buf += chunk
    return json.loads(buf.decode("utf-8"))

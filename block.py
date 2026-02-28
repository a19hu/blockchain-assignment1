"""
Block: previous hash, height, timestamp, list of transactions, block hash.
Mining uses exponential waiting time (PoW simulation).
"""
import json
import time
from crypto_utils import sha256_hash


def block_header_string(prev_hash: str, height: int, timestamp: float, tx_hashes: list) -> str:
    """Canonical string for block hashing."""
    return f"{prev_hash}|{height}|{timestamp}|{','.join(sorted(tx_hashes))}"


def compute_block_hash(prev_hash: str, height: int, timestamp: float, tx_hashes: list) -> str:
    return sha256_hash(block_header_string(prev_hash, height, timestamp, tx_hashes).encode())


def create_block(prev_hash: str, height: int, transactions: list) -> dict:
    """Create a new block. Block hash = SHA256(prev_hash|height|timestamp|tx_hashes)."""
    timestamp = time.time()
    tx_hashes = [t["TxID"] for t in transactions]
    block_hash = compute_block_hash(prev_hash, height, timestamp, tx_hashes)
    return {
        "BlockHash": block_hash,
        "PrevHash": prev_hash,
        "Height": height,
        "Timestamp": timestamp,
        "Transactions": transactions,
        "TxHashes": tx_hashes,
    }


def block_to_bytes(b: dict) -> bytes:
    return json.dumps(b).encode()


def block_from_bytes(data: bytes) -> dict:
    return json.loads(data.decode())

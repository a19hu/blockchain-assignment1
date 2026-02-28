"""
Submit a signed transaction to a peer (for testing).
Usage: python submit_tx.py [host] [port] [receiver_address] [data]
Example: python submit_tx.py 127.0.0.1 8000 0x1a2b "100 barrels delivered to Refinery A"
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wallet import Wallet
from transaction import create_transaction, tx_to_bytes
from protocol import encode_message, read_message
from crypto_utils import sha256_hash
import socket
import time


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    receiver = sys.argv[3] if len(sys.argv) > 3 else "0x0001"
    data = sys.argv[4] if len(sys.argv) > 4 else "100 barrels delivered to Refinery A"
    wallet = Wallet()
    tx = create_transaction(wallet, receiver, data)
    gossip_id = sha256_hash(f"{time.time()}:{host}:0".encode())
    msg = {"type": "GOSSIP_TX", "gossip_id": gossip_id, "tx": tx}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))
        s.send(encode_message(msg))
        print("Submitted TX:", tx["TxID"][:32], "...")
        print("Sender:", tx["SenderAddress"], "Receiver:", receiver, "Data:", data)
        s.close()
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()

"""
Transaction: TxID (SHA-256 of contents), Sender/Receiver addresses, Data, ECDSA signature.
"""
import json
from crypto_utils import sha256_hash, verify_signature
from wallet import Wallet


def tx_content_string(sender: str, receiver: str, data: str) -> str:
    """Canonical string used for TxID and signing."""
    return f"{sender}|{receiver}|{data}"


def compute_txid(sender: str, receiver: str, data: str) -> str:
    """TxID = SHA-256 of transaction contents (avalanche effect)."""
    return sha256_hash(tx_content_string(sender, receiver, data).encode())


def create_transaction(wallet: Wallet, receiver_address: str, data: str) -> dict:
    """
    Create signed transaction. TxID hashes contents; sender signs the content string.
    """
    sender = wallet.address
    content = tx_content_string(sender, receiver_address, data)
    txid = sha256_hash(content.encode())
    sig = wallet.sign(content.encode())
    return {
        "TxID": txid,
        "SenderAddress": sender,
        "ReceiverAddress": receiver_address,
        "Data": data,
        "Signature": sig.hex(),
        "PublicKey": wallet.pk_bytes.hex(),
    }


def verify_transaction(tx: dict) -> bool:
    """Verify ECDSA signature using sender's public key."""
    content = tx_content_string(
        tx["SenderAddress"], tx["ReceiverAddress"], tx["Data"]
    ).encode()
    sig = bytes.fromhex(tx["Signature"])
    pk = bytes.fromhex(tx["PublicKey"])
    return verify_signature(pk, content, sig)


def tx_to_bytes(tx: dict) -> bytes:
    """Serialize transaction for network/gossip."""
    return json.dumps(tx, sort_keys=True).encode()


def tx_from_bytes(data: bytes) -> dict:
    return json.loads(data.decode())

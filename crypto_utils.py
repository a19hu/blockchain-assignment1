"""
Cryptographic utilities for the petroleum supply chain blockchain.
Uses secp256k1 (y^2 = x^3 + 7 mod p) for keys and ECDSA for signatures.
"""
import hashlib
import os
from ecdsa import SECP256k1, SigningKey, VerifyingKey, BadSignatureError


# SECP256k1 curve order (number of points on the curve)
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def generate_secret_key():
    """Generate 256-bit secret key: random bytes -> SHA256 -> integer in [1, n-1]."""
    r = os.urandom(32)
    h = hashlib.sha256(r).digest()
    sk_int = int.from_bytes(h, "big") % (SECP256K1_ORDER - 1) + 1
    return sk_int


def secret_key_to_signing_key(sk_int):
    """Create ECDSA signing key from integer secret (sk * G gives public key)."""
    return SigningKey.from_secret_exponent(sk_int, curve=SECP256k1, hashfunc=hashlib.sha256)


def public_key_to_address(pk_bytes):
    """
    Wallet address = last 16 bits of SHA256(public_key) as 4-digit hex (e.g. 0x9e1c).
    """
    h = hashlib.sha256(pk_bytes).digest()
    last_16_bits = int.from_bytes(h[-2:], "big")  # last 2 bytes
    return "0x{:04x}".format(last_16_bits)


def get_address_from_signing_key(sk):
    """Derive wallet address from signing key (public key -> SHA256 -> last 16 bits)."""
    vk = sk.get_verifying_key()
    pk_bytes = vk.to_string()
    return public_key_to_address(pk_bytes)


def sign_message(sk: SigningKey, message: bytes) -> bytes:
    """Sign message with ECDSA; returns (r,s) as raw 64-byte signature."""
    return sk.sign(message)


def verify_signature(pk_bytes: bytes, message: bytes, signature: bytes) -> bool:
    """Verify ECDSA signature using public key bytes."""
    try:
        vk = VerifyingKey.from_string(pk_bytes, curve=SECP256k1)
        vk.verify(signature, message)
        return True
    except (BadSignatureError, Exception):
        return False


def sha256_hash(data: bytes) -> str:
    """Return SHA-256 hash of data as hex string."""
    return hashlib.sha256(data).digest().hex()

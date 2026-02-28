"""
Cryptographic utilities for the petroleum supply chain blockchain.
Uses secp256k1 (y^2 = x^3 + 7 mod p) for keys and ECDSA for signatures.
"""
import hashlib
import os
from ecdsa import SECP256k1, SigningKey, VerifyingKey, BadSignatureError


# SECP256k1 curve order (number of points on the curve)
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# secp256k1 curve parameters: y^2 = x^3 + 7 (mod p)
SECP256K1_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
SECP256K1_A = 0
SECP256K1_B = 7
SECP256K1_GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
SECP256K1_GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424


def _modinv(k: int, p: int) -> int:
    return pow(k, p - 2, p)


def _point_add(p1: tuple[int, int] | None, p2: tuple[int, int] | None) -> tuple[int, int] | None:
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % SECP256K1_P == 0:
        return None
    if x1 == x2 and y1 == y2:
        s = (3 * x1 * x1 + SECP256K1_A) * _modinv(2 * y1, SECP256K1_P)
    else:
        s = (y2 - y1) * _modinv((x2 - x1) % SECP256K1_P, SECP256K1_P)
    s %= SECP256K1_P
    x3 = (s * s - x1 - x2) % SECP256K1_P
    y3 = (s * (x1 - x3) - y1) % SECP256K1_P
    return (x3, y3)


def _scalar_mult(k: int, point: tuple[int, int] | None) -> tuple[int, int] | None:
    """Double-and-add scalar multiplication (k * point)."""
    if k % SECP256K1_ORDER == 0 or point is None:
        return None
    result = None
    addend = point
    while k > 0:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result


def generate_secret_key():
    """Generate 256-bit secret key: random bytes -> SHA256 -> integer in [1, n-1]."""
    r = os.urandom(32)
    h = hashlib.sha256(r).digest()
    sk_int = int.from_bytes(h, "big") % (SECP256K1_ORDER - 1) + 1
    return sk_int


def secret_key_to_signing_key(sk_int):
    """Create ECDSA signing key from integer secret (sk * G gives public key)."""
    return SigningKey.from_secret_exponent(sk_int, curve=SECP256k1, hashfunc=hashlib.sha256)


def public_key_from_secret_key(sk_int: int) -> bytes:
    """
    Derive public key (pk = sk * G) using Double-and-Add on secp256k1.
    Returns raw 64-byte (x||y) public key bytes.
    """
    point = _scalar_mult(sk_int, (SECP256K1_GX, SECP256K1_GY))
    if point is None:
        raise ValueError("Invalid secret key for public key derivation.")
    x, y = point
    return x.to_bytes(32, "big") + y.to_bytes(32, "big")


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

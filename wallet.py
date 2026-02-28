"""
Wallet: holds secret key, public key, and 16-bit hex address.
Secret key is derived from SHA256(random); address from last 16 bits of SHA256(pk).
"""
import json
from crypto_utils import (
    generate_secret_key,
    secret_key_to_signing_key,
    get_address_from_signing_key,
    sign_message,
)
from ecdsa import SigningKey


class Wallet:
    def __init__(self, sk_int=None):
        if sk_int is None:
            sk_int = generate_secret_key()
        self.sk_int = sk_int
        self._signing_key: SigningKey = secret_key_to_signing_key(sk_int)
        self.address = get_address_from_signing_key(self._signing_key)
        self.pk_bytes = self._signing_key.get_verifying_key().to_string()

    def sign(self, message: bytes) -> bytes:
        return sign_message(self._signing_key, message)

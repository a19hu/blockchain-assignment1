"""
Task 5: Bit Commitment in Supply Chain
Producer commits to delivery volume m with nonce r: C = H(m || r) in Exploration.
Reveals (m, r) in Refining; anyone can verify C == H(m || r).
Hiding: commitment does not reveal m. Binding: cannot change m after committing.
"""
import hashlib
import os


def H(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def commit(volume: int, nonce: bytes) -> bytes:
    """Commitment C = H(m || r). volume m, nonce r."""
    m = str(volume).encode()
    return H(m + nonce)


def verify(volume: int, nonce: bytes, commitment: bytes) -> bool:
    return commit(volume, nonce) == commitment


def main():
    # Exploration phase: producer commits to 100 barrels
    m = 100  # volume
    r = os.urandom(32)  # nonce
    C = commit(m, r)
    print("Exploration phase: Producer commits to delivery volume.")
    print("  Commitment C = H(m || r):", C.hex()[:32], "...")
    print("  (m and r are not revealed yet.)")
    # Refining phase: reveal
    print("\nRefining phase: Producer reveals m =", m, ", nonce r (32 bytes).")
    ok = verify(m, r, C)
    print("  Verification C == H(m||r):", ok)
    # Binding: trying to claim different volume fails
    ok2 = verify(150, r, C)
    print("  Claiming 150 barrels with same C:", ok2, "(should be False)")
    print("\nHiding: C does not reveal m. Binding: cannot open C to a different m.")
    print("This resolves disputes: producer cannot later claim a different volume.")


if __name__ == "__main__":
    main()

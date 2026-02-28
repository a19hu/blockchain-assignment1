"""
Task 1: The Avalanche Effect
Compute SHA-256 of a transaction string, change one character, recompute.
Report percentage of bits changed.
"""
import hashlib


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def bit_difference_hex(h1: str, h2: str) -> float:
    """Percentage of bits that differ between two hex hashes."""
    b1 = bytes.fromhex(h1)
    b2 = bytes.fromhex(h2)
    total_bits = len(b1) * 8
    diff_bits = sum(bin(x ^ y).count("1") for x, y in zip(b1, b2))
    return 100.0 * diff_bits / total_bits


def main():
    tx1 = "Alice pays Bob $10"
    tx2 = "Alice pays Bob $11"  # one character changed
    h1 = sha256_hex(tx1)
    h2 = sha256_hex(tx2)
    pct = bit_difference_hex(h1, h2)
    print("Original string:", repr(tx1))
    print("Hash 1:", h1)
    print("Changed string:", repr(tx2))
    print("Hash 2:", h2)
    print(f"Percentage of bits changed: {pct:.2f}%")
    print("\nThis avalanche effect supports tamper-resistance: a tiny change")
    print("in the input produces a completely different hash, so tampering")
    print("is immediately detectable.")


if __name__ == "__main__":
    main()

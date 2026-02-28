"""
Task 2: Merkle Tree for 8 transactions; Merkle Proof for 4th transaction.
"""
import hashlib


def H(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def build_merkle_root(tx_hashes: list[bytes]) -> bytes:
    """Build Merkle tree from list of transaction hashes; return root."""
    if not tx_hashes:
        return H(b"")
    level = list(tx_hashes)
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            next_level.append(H(left + right))
        level = next_level
    return level[0]


def merkle_proof(tx_hashes: list[bytes], index: int) -> tuple[bytes, list[tuple[bytes, str]]]:
    """
    Return (leaf_hash, proof_list).
    proof_list: [(sibling_hash, "L"|"R")] where L means sibling is on left.
    """
    if index < 0 or index >= len(tx_hashes):
        raise ValueError("index out of range")
    leaf = tx_hashes[index]
    level = list(tx_hashes)
    proof = []
    idx = index
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            parent = H(left + right)
            next_level.append(parent)
            if i == idx:
                proof.append((right, "R"))  # sibling on right
            elif i + 1 == idx:
                proof.append((left, "L"))   # sibling on left
        idx = idx // 2
        level = next_level
    return leaf, proof


def verify_merkle_proof(leaf: bytes, proof: list[tuple[bytes, str]], root: bytes) -> bool:
    current = leaf
    for sibling, side in proof:
        if side == "L":
            current = H(sibling + current)
        else:
            current = H(current + sibling)
    return current == root


def main():
    # 8 transactions (as hashes of strings)
    txs = [f"tx_{i}".encode() for i in range(8)]
    tx_hashes = [H(t) for t in txs]
    root = build_merkle_root(tx_hashes)
    print("Merkle root (hex):", root.hex())
    # Proof for 4th transaction (index 3)
    leaf, proof = merkle_proof(tx_hashes, 3)
    print("\nMerkle proof for 4th transaction (index 3):")
    for i, (sib, side) in enumerate(proof):
        print(f"  Step {i+1}: sibling ({side}): {sib.hex()[:32]}...")
    ok = verify_merkle_proof(leaf, proof, root)
    print("\nVerify proof:", ok)
    print("\nA Light Node only needs the block header (with Merkle root) plus")
    print("O(log n) hashes for the proof, instead of downloading all n transactions.")


if __name__ == "__main__":
    main()

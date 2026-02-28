# CSL7490 Assignment 1: Petroleum Supply Chain Blockchain

Blockchain-based petroleum supply chain ledger on a P2P network (Seed nodes + Peer nodes).

## Description

This project implements a blockchain-backed petroleum supply chain ledger on top of a P2P network.
The network consists of seed nodes (for discovery and registration) and peer nodes (for gossiping,
transaction validation, liveness checks, and PoW-style block mining). Each node uses secp256k1 keys,
derives a 16-bit wallet address from SHA-256 of the public key, and signs transactions with ECDSA.
Blocks are mined via an exponential waiting time based on each miner’s hash power.

## Requirements

- Python 3.8+
- `ecdsa`: `pip install ecdsa`
- Optional for Task 7 plots: `pip install matplotlib`

## Project Layout

- `crypto_utils.py` — secp256k1, SHA-256, address (last 16 bits of SHA256(pk)), Double-and-Add pk derivation, ECDSA sign/verify
- `wallet.py` — key generation (SHA256(random) → sk), address derivation
- `transaction.py` — TxID = SHA256(contents), ECDSA signature
- `block.py` — block structure and hash
- `block_db.py` — SQLite storage for blocks
- `config.py` — seed ports, interarrival time, liveness interval
- `protocol.py` — length-prefixed JSON over TCP
- `seed_node.py` — seed process
- `peer_node.py` — peer: register with seeds, connect to ≥4 peers, gossip, liveness, PoW mining
- `submit_tx.py` — submit a transaction to a peer (for testing)
- `experiments/` — Task 1–7 scripts and answers

## How to Run

### 0. Setup (Install Dependencies)

```bash
python -m pip install -r requirements.txt
```

If `requirements.txt` is not used, install manually:

```bash
python -m pip install ecdsa matplotlib
```

### 1. Start seed nodes (at least ⌊n/2⌋+1 for n seeds)

```bash
# Terminal 1, 2, 3
python seed_node.py 9000
python seed_node.py 9001
python seed_node.py 9002
```

### 2. Start peer nodes (each connects to seeds, gets peer list, connects to ≥4 peers)

```bash
# Terminal 4, 5, 6, 7 (use different ports)
python peer_node.py 8000 10
python peer_node.py 8001 10
python peer_node.py 8002 10
python peer_node.py 8003 15
```

Second argument is hash power percentage (default 10). For Task 4 (51%) run one peer with `51`.

### 3. Submit a transaction

```bash
python submit_tx.py 127.0.0.1 8000 0x0001 "100 barrels delivered to Refinery A"
```

Peers will gossip the TX, validate the signature, and miners will include it in the next block (exponential waiting time).

### 4. Run Experimental Tasks (Optional)

```bash
python experiments/task1_avalanche.py
python experiments/task2_merkle.py
python experiments/task3_double_spend.py
python experiments/task4_51_percent.py
python experiments/task5_commitment.py
python experiments/task6_target_leading_zeros.py
python experiments/task7_stochastic.py
```

## Experimental Tasks (Run and Report)

- **Task 1 — Avalanche:** `python experiments/task1_avalanche.py`  
  Answer: A one-character change flips ~50% of hash bits. This makes tampering detectable: any change in the transaction changes the hash completely.

- **Task 2 — Merkle proof:** `python experiments/task2_merkle.py`  
  Answer: A light node only needs the block header (Merkle root) and O(log n) sibling hashes for one transaction instead of the full block body (all n transactions).

- **Task 3 — Double-spending:** See `experiments/task3_double_spend.py`.  
  Answer: The public ledger records one ordering; consensus (longest chain) ensures only one of two conflicting deliveries (same 100 barrels to two refineries) is confirmed.

- **Task 4 — 51% mining:** See `experiments/task4_51_percent.py`.  
  Answer: With one entity at 51% hash power, Security (risk of reorg/double-spend) and Decentralisation (single point of control) decrease; the trilemma trade-off is visible.

- **Task 5 — Bit commitment:** `python experiments/task5_commitment.py`  
  Answer: Hiding: C = H(m∥r) does not reveal m. Binding: cannot open to a different m. This lets a producer commit in Exploration and reveal in Refining without coordination disputes.

- **Task 6 — Target and leading zeros:** See `experiments/task6_target_leading_zeros.py`.  
  Answer: For target T, valid hash &lt; T implies a required number of leading zero bits (≈ 256 − log₂(T)). More leading zeros ⇒ harder puzzle ⇒ lower block rate ⇒ smaller λ ⇒ larger average τ in our simulation.

- **Task 7 — Stochastic analysis:** `python experiments/task7_stochastic.py`  
  Answer: For fixed hash power, Tk is exponential (histogram matches Exp(λ)). As hash power (and thus λ) increases, average waiting time 1/λ decreases.

## Design Notes

- **Registration:** Peer sends `REGISTER` with its port to each seed; seeds maintain a peer list (PL).
- **P2P:** Peer fetches PL from seeds, takes union, connects to at least 4 distinct peers over TCP.
- **Gossip:** Messages like `<timestamp>:<IP>:<Msg#>`; nodes keep a message list (ML) of hashes, validate (e.g. TX signature), then forward to all neighbours except sender.
- **Liveness:** Every 13 s nodes send a liveness request; 3 consecutive failures → report “Dead Node” to seeds and close connection.
- **Mining:** On receiving a block at time t, miner samples τ ~ Exp(λ) with λ = (hash_power/100)*meanTk; if no better block by t+τ, it creates and broadcasts a block. New nodes sync from genesis to latest height then process pending queue.

## Submission

Code and report in a single archive: `rollno1-rollno2.tar.gz`. One member uploads to Google Classroom.

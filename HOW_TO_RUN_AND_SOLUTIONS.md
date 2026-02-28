# How to Run, Test, and Solutions for All 7 Questions

---

## Part 1: How to Run and Test

### Prerequisites

```bash
cd /Users/mayankbansal/Desktop/blockchain-1
pip install ecdsa
# Optional (for Task 7 plots only):
pip install matplotlib
```

### Step 1: Start 3 seed nodes (use 3 separate terminals)

```bash
# Terminal 1
python seed_node.py 9000

# Terminal 2
python seed_node.py 9001

# Terminal 3
python seed_node.py 9002
```

You should see each seed print: `[Seed:9000] Listening on port 9000` (and 9001, 9002).

### Step 2: Start 4 peer nodes (use 4 more terminals)

```bash
# Terminal 4
python peer_node.py 8000 10

# Terminal 5
python peer_node.py 8001 10

# Terminal 6
python peer_node.py 8002 10

# Terminal 7
python peer_node.py 8003 10
```

- First number = port (8000, 8001, 8002, 8003).
- Second number = hash power % (10 = 10%). For Task 4 (51% scenario), run one peer as: `python peer_node.py 8000 51`.

Each peer should print: Registered with 2 seeds, Connected to 4 peers, Listening on &lt;port&gt;. When a block is mined you’ll see: `[Peer 8000] Mined block height=1`.

### Step 3: Submit a transaction (new terminal)

```bash
python submit_tx.py 127.0.0.1 8000 0x0001 "100 barrels delivered to Refinery A"
```

- `127.0.0.1 8000` = peer to send the TX to.
- `0x0001` = receiver address (any 4-digit hex).
- Last argument = transaction data (e.g. supply chain event or “Alice pays Bob $10”).

The TX is gossiped, verified (signature), and included in the next block. Check any peer terminal for “Mined block height=…” after a short random delay.

### Step 4: Run the 7 experiment scripts (no seeds/peers needed)

From the project root:

```bash
python experiments/task1_avalanche.py
python experiments/task2_merkle.py
python experiments/task3_double_spend.py
python experiments/task4_51_percent.py
python experiments/task5_commitment.py
python experiments/task6_target_leading_zeros.py
python experiments/task7_stochastic.py
```

Task 7 will show/save plots if `matplotlib` is installed.

---

## Part 2: Solutions to All 7 Questions

### Question 1: The Avalanche Effect

**Task:** Hash a transaction string, change one character, hash again. What % of bits changed? How does this support tamper-resistance?

**Solution:**

- **Percentage of bits changed:** Run `python experiments/task1_avalanche.py`; typically **about 50%** of the bits in the second hash differ from the first.
- **Tamper-resistance:** A tiny change in the input (one character) produces a completely different hash. So any tampering with the transaction or block is immediately detectable: the recomputed hash will not match the stored one.

---

### Question 2: Merkle Proof Efficiency

**Task:** Build a Merkle tree for 8 transactions and give the Merkle proof for the 4th. Why is a Merkle proof more efficient for a light node?

**Solution:**

- **Run:** `python experiments/task2_merkle.py` to get the tree, root, and proof for the 4th transaction.
- **Efficiency:** A light node only needs the **block header** (with Merkle root) plus **O(log n)** sibling hashes along the path from the leaf to the root—instead of downloading the **entire block body** (all n transactions). So bandwidth and storage are much smaller when verifying a single transaction.

---

### Question 3: Double-Spending Prevention

**Task:** Simulate an upstream producer recording the same 100 barrels as delivered to two refineries. How do the ledger and consensus prevent this?

**Solution:**

- **Run:** `python experiments/task3_double_spend.py` for the narrative.
- **How it’s prevented:**
  - **Public ledger:** Everyone sees the same ordered list of transactions.
  - **Consensus (e.g. longest chain):** Only one canonical history is chosen. Only one of the two conflicting deliveries (same 100 barrels to two refineries) can be in that history.
  - Once a block is confirmed, that asset is “spent”; the other conflicting transaction is invalid or ignored. So the same 100 barrels cannot be recorded as delivered twice.

---

### Question 4: 51% Mining and the Trilemma

**Task:** Simulate one node with 51% hash power. What happens to Security and Decentralisation?

**Solution:**

- **Run:** `python experiments/task4_51_percent.py` for the explanation. To see it in the main code, run one peer with 51%: `python peer_node.py 8000 51` and others with lower %.
- **Security:** The 51% miner can reorg the chain, double-spend, or censor transactions. Security (honest-majority assumption) is reduced.
- **Decentralisation:** Control is concentrated in one entity; the network is no longer meaningfully decentralised.
- **Trilemma:** Giving one entity majority hash power trades away Security and Decentralisation (e.g. for higher throughput or fewer forks).

---

### Question 5: Bit Commitment in Supply Chain

**Task:** Implement C = H(m∥r); commit in Exploration, reveal in Refining. How do Hiding and Binding resolve disputes?

**Solution:**

- **Run:** `python experiments/task5_commitment.py` to see commit/verify and binding (can’t open to different m).
- **Hiding:** C = H(m∥r) does not reveal the volume m until reveal. The producer can commit in the Exploration phase without revealing the amount.
- **Binding:** After committing, the producer cannot change m: opening to a different m′ would require finding r′ with H(m′∥r′) = C, which is infeasible. So neither party can later claim a different value, which resolves coordination disputes.

---

### Question 6: Target Variable and Leading Zeros

**Task:** For a given target T, how many leading zero bits are required? How does increasing them affect λ and τ in our simulation?

**Solution:**

- **Run:** `python experiments/task6_target_leading_zeros.py` for the full text.
- **Leading zeros:** If the hash must be less than target T, valid hashes are in [0, T). The number of leading zero bits required is approximately **k = 256 − ⌊log₂(T)⌋** (for a 256-bit hash).
- **Effect on λ and τ:** More leading zeros ⇒ harder puzzle ⇒ longer average block time network-wide ⇒ smaller mean block rate ⇒ **smaller λ** for each miner ⇒ **larger** average waiting time **τ** (since τ ∝ 1/λ in our simulation).

---

### Question 7: Stochastic Analysis of Mining

**Task:** For fixed hash power, collect Tk over 100 cycles and plot; plot λ vs hash power %. How does Tk behave as hash power (λ) increases?

**Solution:**

- **Run:** `python experiments/task7_stochastic.py` (uses matplotlib if installed).
- **Behaviour:**  
  - **λ = (nodeHashPower × meanTk) / 100**, so higher hash power ⇒ higher λ.  
  - **Average waiting time = 1/λ**, so higher λ ⇒ shorter average Tk.  
  - As a node’s hash power increases, it finds blocks more often (smaller Tk on average). The histogram of Tk for a fixed hash power follows an **exponential distribution**.

---

## Quick Reference: Commands

| What to do              | Command |
|-------------------------|--------|
| Seed 1                  | `python seed_node.py 9000` |
| Seed 2                  | `python seed_node.py 9001` |
| Seed 3                  | `python seed_node.py 9002` |
| Peer 1 (10% hash)       | `python peer_node.py 8000 10` |
| Peer 2–4                | `python peer_node.py 8001 10` (and 8002, 8003) |
| Submit TX               | `python submit_tx.py 127.0.0.1 8000 0x0001 "100 barrels to Refinery A"` |
| Task 1–7 (experiments)  | `python experiments/task1_avalanche.py` … `task7_stochastic.py` |

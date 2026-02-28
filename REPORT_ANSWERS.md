# Assignment 1 — Analytical / Report Answers

Use these for the written report.

---

## Task 1: The Avalanche Effect

**What percentage of the bits changed in the second hash?**  
Typically around **50%** of the bits change when one character is changed (run `python experiments/task1_avalanche.py` to get the exact value).

**How does this property support tamper-resistance?**  
Any change in the input (even a single bit) produces a completely different hash. So tampering with a transaction or block is immediately detectable: the recomputed hash will not match the stored one.

---

## Task 2: Merkle Proof Efficiency

**Why is providing a Merkle Proof more efficient for a Light Node than downloading the entire block body?**  
A light node only needs the block header (which includes the Merkle root) and **O(log n)** sibling hashes along the path from the leaf to the root—instead of all **n** transactions. So bandwidth and storage are much smaller when verifying a single transaction.

---

## Task 3: Double-Spending Prevention

**How do the Public Trusted Bulletin Board (ledger) and consensus prevent double spending?**  
- The **ledger** is public and ordered: every participant sees the same sequence of transactions.  
- **Consensus** (e.g. longest chain) fixes a single canonical history. Only one of two conflicting transactions (same 100 barrels to two refineries) can be in that history.  
- Once a block is confirmed, the asset is “spent”; the other conflicting transaction is invalid or ignored. So the same asset cannot be spent twice.

---

## Task 4: 51% Hash Power and the Trilemma

**What happens to Security and Decentralisation if one entity controls the majority of computing power?**  
- **Security:** The 51% miner can reorg the chain, double-spend, or censor transactions. Security (assumption of honest majority) is reduced.  
- **Decentralisation:** Control is concentrated in one entity; the network is no longer meaningfully decentralised.  
- **Trilemma:** Increasing centralisation of hash power trades away Security and Decentralisation (e.g. for higher throughput or fewer forks).

---

## Task 5: Bit Commitment (Hiding and Binding)

**How do Hiding and Binding resolve coordination disputes between mutually distrustful parties?**  
- **Hiding:** The commitment C = H(m∥r) does not reveal the volume m until reveal. The producer can commit in the Exploration phase without giving away the amount.  
- **Binding:** After committing, the producer cannot change m: opening to a different m′ would require finding r′ with H(m′∥r′) = C, which is infeasible. So neither party can cheat by changing the committed value later, which resolves disputes about what was agreed.

---

## Task 6: Target Variable and Leading Zeros

**For a given target T, how many bits of leading zeros are required?**  
If the hash must be less than target T, then valid hashes lie in [0, T). So the number of leading zero bits is (approximately) **k = 256 − ⌊log₂(T)⌋** (when viewing the hash as a 256-bit integer).

**How would an increase in required leading zero bits affect λ and τ in our simulation?**  
More leading zeros ⇒ harder puzzle ⇒ **longer** average block time network-wide ⇒ **smaller** mean block rate ⇒ **smaller λ** for each miner ⇒ **larger** average waiting time τ (= 1/λ for each miner).

---

## Task 7: Stochastic Analysis

**How does the exponential waiting time behave as hash power increases?**  
- **λ = (nodeHashPower × meanTk) / 100**, so higher hash power ⇒ higher λ.  
- **Average waiting time = 1/λ**, so higher λ ⇒ **shorter** average Tk.  
- So as a node’s hash power increases, it finds blocks more frequently (smaller Tk on average). The histogram of Tk for a fixed hash power follows an exponential distribution.

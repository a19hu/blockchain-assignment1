"""
Task 3: Double-Spending Simulation
Upstream Producer attempts to record same 100 barrels as delivered to two refineries.
The ledger and consensus prevent this.
"""
print("""
=== Double-Spending Simulation (Conceptual) ===

Scenario: Upstream Producer tries to record:
  - "100 barrels delivered to Refinery A"
  - "100 barrels delivered to Refinery B"
  (same 100 barrels, two recipients)

How the system prevents it:

1. PUBLIC TRUSTED BULLETIN BOARD (Ledger):
   - Every transaction is recorded and visible to all participants.
   - If the producer broadcasts both transactions, nodes see two deliveries
     of the same 100 barrels. The ledger state (e.g. who owns what) would
     be inconsistent if both were accepted.

2. CONSENSUS MECHANISM:
   - Only one ordering of transactions is agreed (e.g. longest chain).
   - Miners include transactions in blocks; once a block is finalized,
     the transaction is settled. The other conflicting transaction
     (same asset, different recipient) is rejected or ignored by the
     protocol (e.g. double-spend of same UTXO invalid).

3. RESULT:
   - At most one of "100 barrels to A" or "100 barrels to B" can appear
     in the canonical chain. The other is discarded or never confirmed.
   - Thus the producer cannot spend the same 100 barrels twice.

Run the main blockchain (seed + peers) and submit two conflicting
transactions to see only one confirmed.
""")

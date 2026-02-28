"""
Task 4: Mining Power and Forks — 51% hash power.
Blockchain Trilemma: Security, Decentralisation, Scalability.
"""
print("""
=== 51% Hash Power and the Blockchain Trilemma ===

If one node has 51% of total hash power:

1. SECURITY:
   - The 51% entity can dominate block production and potentially perform
     double-spending attacks (reorg the chain to exclude a payment and
     include a conflicting one). They can also censor transactions.
   - Security of the chain is reduced because the assumption "honest
     majority of hash power" is violated.

2. DECENTRALISATION:
   - Decentralisation is severely reduced: one entity controls the
     majority of mining. Decisions (which blocks get built on, which
     txs get included) are effectively in one hand.
   - The network is no longer "trustless" in the same way—participants
     must trust that the 51% miner does not abuse power.

3. TRADE-OFF:
   - The trilemma says you cannot maximise Security, Decentralisation,
     and Scalability at once. Here, concentrating hash power improves
     (temporarily) consistency and possibly throughput (fewer forks)
     but at the cost of Security and Decentralisation.

To simulate: run the main peer_node with hash_power=51 and others with
lower power; over time the 51% node will mine more blocks.
""")

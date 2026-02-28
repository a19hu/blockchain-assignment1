"""
Task 6: Target Variable and Leading Zeros
Relationship between PoW target, leading zero bits, and our simulation (lambda, tau).
"""
print("""
=== Target Variable and Leading Zeros in PoW ===

1. STANDARD PoW:
   - Target T is a 256-bit value. A valid block hash must be < T.
   - Often expressed as "difficulty D": T = T_max / D (e.g. max target has
     many leading 1s; lowering T means hash must be smaller).
   - Leading zeros: If T is chosen so that valid hashes are in [0, 2^(256-k)),
     then a valid hash has at least k leading zero bits (when written in
     fixed 256-bit form). So:
       T = 2^(256 - k)  =>  need k leading zero bits.
   - For a given target T (as integer), the number of leading zero bits
     required is approximately: k = 256 - floor(log2(T)).
     (More precisely: hash has leading zeros until the first 1 in the
     most significant bits; expected "difficulty" in tries is 2^k.)

2. EFFECT ON LAMBDA AND WAITING TIME:
   - In real PoW, expected time to find a block = (2^k * block_time_per_hash).
   - In our simulation we do not model bits; we directly use an exponential
     waiting time with rate lambda. So:
     - Increasing difficulty (more leading zeros) in real PoW => fewer
       blocks per unit time => longer average interarrival time.
     - In our model: interarrival_time is fixed (e.g. 30s). So meanTk = 1/30.
       lambda_i = (hash_power_i/100) * meanTk.
     - If we were to model "increase in required leading zeros", we would
       decrease meanTk (longer average block time network-wide), so meanTk
       would get smaller => lambda for each miner would decrease =>
       waiting time tau = Exp(1)/lambda would increase (miners wait longer
       per block on average).
   - Summary: More leading zero bits => harder puzzle => lower effective
     block rate => smaller lambda => larger average tau.
""")

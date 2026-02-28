"""
Configuration: seed ports, interarrival time, liveness interval, etc.
"""
# Number of seed nodes in the network (for registration: need floor(n/2)+1)
NUM_SEEDS = 3
SEED_PORTS = [9000, 9001, 9002]

# Block mining: interarrival time (seconds) for the whole network
INTERARRIVAL_TIME = 30.0  # mean time between blocks network-wide

# Liveness: exchange every 13 seconds; dead after 3 consecutive failures
LIVENESS_INTERVAL = 13
LIVENESS_FAIL_THRESHOLD = 3

# Block timestamp valid if within ±1 hour of current time
BLOCK_TIME_TOLERANCE = 3600  # seconds

# Min peers to connect to (assignment: at least 4)
MIN_PEERS = 4

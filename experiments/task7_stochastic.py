"""
Task 7: Stochastic Analysis of Mining
1. For fixed hash power, collect Tk over 100 mining cycles; plot histogram/PDF.
2. Plot lambda vs hash power (1% to 100%) for constant meanTk.
"""
import random
import math

# Try to use matplotlib; if not installed, print numeric results only
try:
    import matplotlib.pyplot as plt
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

INTERARRIVAL_TIME = 30.0
mean_tk = 1.0 / INTERARRIVAL_TIME


def waiting_time(hash_power_pct: float) -> float:
    """One sample of Tk = Exp(1)/lambda, lambda = nodeHashPower*meanTk/100."""
    lam = hash_power_pct * mean_tk / 100.0
    if lam <= 0:
        return 999.0
    return random.expovariate(lam)


def main():
    # 1. Fixed hash power (e.g. 10%), 100 samples of Tk
    hash_power = 10.0
    samples = [waiting_time(hash_power) for _ in range(100)]
    avg = sum(samples) / len(samples)
    print(f"Fixed hash power = {hash_power}%")
    print(f"100 samples of Tk: mean = {avg:.2f}s, theoretical 1/lambda = {100.0 / (hash_power * mean_tk):.2f}s")

    if HAS_PLOT:
        plt.figure(figsize=(10, 4))
        plt.subplot(1, 2, 1)
        plt.hist(samples, bins=20, density=True, alpha=0.7, edgecolor="black", label="Tk samples")
        plt.xlabel("Waiting time Tk (s)")
        plt.ylabel("Density")
        plt.title(f"Waiting time distribution (hash power = {hash_power}%)")
        plt.legend()
    else:
        print("(Install matplotlib to get histogram plot.)")

    # 2. Lambda vs hash power (1% to 100%)
    powers = list(range(1, 101))
    lambdas = [p * mean_tk / 100.0 for p in powers]
    avg_waits = [1.0 / lam for lam in lambdas]

    print("\nLambda vs hash power (meanTk = 1/30):")
    print("  Hash power 10% -> lambda =", 10 * mean_tk / 100, "-> avg Tk =", 1 / (10 * mean_tk / 100))
    print("  Hash power 51% -> lambda =", 51 * mean_tk / 100, "-> avg Tk =", 1 / (51 * mean_tk / 100))

    if HAS_PLOT:
        plt.subplot(1, 2, 2)
        plt.plot(powers, lambdas, "b-")
        plt.xlabel("Hash power (%)")
        plt.ylabel("Lambda")
        plt.title("Lambda vs hash power (constant meanTk)")
        plt.tight_layout()
        plt.savefig("task7_plots.png", dpi=150)
        print("\nSaved task7_plots.png")
        plt.show()
    print("\nAs hash power increases, lambda increases, so average waiting time 1/lambda decreases.")
    print("Higher lambda => miner finds blocks more frequently.")


if __name__ == "__main__":
    main()

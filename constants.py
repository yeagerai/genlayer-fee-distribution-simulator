import random
import string
import hashlib


def generate_random_address() -> str:
    """
    Generate a random Ethereum-style address.

    Returns:
        A random Ethereum address string
    """
    # Create random string as seed
    seed = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    # Hash it with SHA-256
    hashed = hashlib.sha256(seed.encode()).hexdigest()
    # Format as Ethereum address (0x + 40 hex chars)
    return "0x" + hashed[:40]


# Round sizes (odd indexes are appeal rounds)
round_sizes = [
    5,
    7,
    11,
    13,
    23,
    25,
    47,
    49,
    95,
    97,
    191,
    193,
    383,
    385,
    767,
    769,
    1535,
]

penalty_reward_coefficient = 2

# Generate pool of 2000 random addresses
addresses_pool = [generate_random_address() for _ in range(2000)]

# Initialize empty fee distribution dictionary
# This is used as a starting point for fee distribution calculations
# Note: In actual use, create a FeeDistribution model with these entries
fee_distribution = {}
for addr in addresses_pool:
    fee_distribution[addr] = {
        "leader": 0,
        "leader_node": 0,
        "validator_node": 0,
        "sender": 0,
        "sender_node": 0,
        "appealant": 0,
        "appealant_node": 0,
    }

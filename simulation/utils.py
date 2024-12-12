# simulation/utils.py

import random
import numpy as np

from simulation.config_constants import MAX_NUM_VALS, MIN_NUM_VALS


def generate_ethereum_address() -> str:
    """
    Generate a random Ethereum-like address.

    Returns:
        str: A 40-character hexadecimal string prefixed with '0x', simulating an Ethereum address.
    """
    address = "0x" + "".join(random.choices("0123456789abcdef", k=40))
    return address


def generate_validators_per_round_sequence() -> list[int]:
    """
    Generate a sequence of validator counts for successive rounds.

    The sequence follows the pattern: n -> 2n + 1, starting from MIN_NUM_VALS
    and not exceeding MAX_NUM_VALS. The final number in the sequence will always
    be MAX_NUM_VALS.

    Example:
        If MIN_NUM_VALS = 3 and MAX_NUM_VALS = 15, returns [3, 7, 15]
        Because: 3 -> 7 -> 15 (each number is 2n + 1 of the previous)

    Returns:
        List[int]: Sequence of validator counts for each round
    """
    sequence = [MIN_NUM_VALS]

    while sequence[-1] < MAX_NUM_VALS:
        next_number = 2 * sequence[-1] + 1
        if next_number >= MAX_NUM_VALS:
            break
        sequence.append(next_number)

    if sequence[-1] != MAX_NUM_VALS:
        sequence.append(MAX_NUM_VALS)

    return sequence


def set_random_seed(seed_value: int) -> None:
    """
    Set the random seed for both Python's random and NumPy's random number generators.

    This ensures reproducible results across different runs of the simulation.

    Args:
        seed_value: Integer value to use as the random seed
    """
    random.seed(seed_value)
    np.random.seed(seed_value)

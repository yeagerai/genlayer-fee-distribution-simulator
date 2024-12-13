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


def calculate_appeal_rounds_budget(num_rounds: int) -> int:
    """
    Helper function to calculate total appeal rounds budget.

    Args:
        num_rounds: Number of appeal rounds supported (security budget set by the user)

    Returns:
        int: Total gas budget needed for appeal rounds
    """
    # That should take into account that appeals escalate validator count
    # and that there are three different types of appeals
    # so each type has a different cost for the user, so just with the number of rounds
    # we must compute the maximum cost so the appeal type that is most expensive

    max_cost = ...

    return num_rounds * max_cost

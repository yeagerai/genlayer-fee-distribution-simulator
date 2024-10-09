# simulation/validator_selection.py
import random

import numpy as np

from simulation.models import Leader
from simulation.utils import generate_ethereum_address


def initialize_validators_list(validators_list, leader_decision):
    """Initializes the leader and validators for the simulation."""
    # Use the first validator as the leader
    leader = Leader(
        id=validators_list[0].id,
        stake=validators_list[0].stake,
        decision=leader_decision,
    )
    # The rest are validators
    validators = validators_list[1:]
    return leader, validators


def generate_validators_pool(N=1000, total_supply=42000000000):
    stakes = (
        np.random.dirichlet(np.ones(N)) * total_supply * 0.7
    )  # 0.7 because is before inflation
    vals_pool = []
    for i in range(N):
        address = generate_ethereum_address()
        stake = stakes[i]
        vals_pool.append([address, stake])
    return vals_pool


def select_validators(N, vals_pool, gamma=0.1):
    """Selects N validators from the validator pool based on their stakes using a softmax function."""
    # Extract the stakes from the validator pool
    stakes = np.array([val[1] for val in vals_pool])

    # Calculate the probability for each validator based on the softmax formula
    adjusted_stakes = stakes**gamma
    probabilities = adjusted_stakes / np.sum(adjusted_stakes)

    # Select N validators based on these probabilities
    selected_indices = np.random.choice(
        len(vals_pool), size=N, replace=False, p=probabilities
    )

    # Return the list of selected validators as [address, stake]
    selected_vals = [vals_pool[i] for i in selected_indices]

    return selected_vals

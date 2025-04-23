from functools import partial
from math import ceil

from fee_simulator.models.custom_types import (
    FeeDistribution,
    FeeEntry,
    TransactionBudget,
)
from fee_simulator.models.constants import (
    round_sizes,
    penalty_reward_coefficient,
    addresses_pool,
)


def initialize_fee_distribution() -> FeeDistribution:
    """Initialize a new fee distribution object."""
    fee_entries = {addr: FeeEntry() for addr in addresses_pool}
    return FeeDistribution(fees=fee_entries)


def compute_total_cost(transaction_budget: TransactionBudget) -> int:
    if transaction_budget.appealRounds == 0:
        num_rounds = 1
    else:
        num_rounds = transaction_budget.appealRounds * 2
    total_cost = 0
    for i in range(num_rounds):
        if i % 2 == 0:
            num_rotations = transaction_budget.rotations[i // 2]
        else:
            num_rotations = 1
        total_cost += (num_rotations + 1) * (
            transaction_budget.leaderTimeout
            + round_sizes[i] * transaction_budget.validatorsTimeout
        )
    return total_cost


def compute_total_fees(fee_entry: FeeEntry) -> int:
    """Compute total fees for a FeeEntry, excluding stake."""
    return (
        fee_entry.leader_node
        + fee_entry.validator_node
        + fee_entry.sender_node
        + fee_entry.appealant_node
    )


def compute_appeal_bond(
    normal_round_index: int,
    round_sizes: list[int],
    penalty_reward_coefficient: int,
    leader_timeout: int,
    validators_timeout: int,
) -> int:
    """
    Compute appeal bond for a specific normal round's appeal.
    """
    safety_coefficient = 1.2

    if (
        normal_round_index % 2 != 0
        or normal_round_index < 0
        or normal_round_index >= len(round_sizes)
    ):
        raise ValueError(f"Invalid normal round index: {normal_round_index}")

    normal_size = round_sizes[normal_round_index]
    appeal_size = (
        round_sizes[normal_round_index + 1]
        if normal_round_index + 1 < len(round_sizes)
        else 0
    )
    next_normal_size = (
        round_sizes[normal_round_index + 2]
        if normal_round_index + 2 < len(round_sizes)
        else 0
    )

    base_penalty = penalty_reward_coefficient * validators_timeout
    appeal_cost = appeal_size * validators_timeout
    next_cost = next_normal_size * validators_timeout

    total_cost = appeal_cost + next_cost + leader_timeout

    minority_size = normal_size // 2
    penalty_offset = minority_size * base_penalty

    appeal_bond = ceil((total_cost - penalty_offset) * safety_coefficient)
    return max(appeal_bond, 0)


# Partial function with fixed round_sizes and penalty_reward_coefficient
compute_appeal_bond_partial = partial(
    compute_appeal_bond,
    round_sizes=round_sizes,
    penalty_reward_coefficient=penalty_reward_coefficient,
)

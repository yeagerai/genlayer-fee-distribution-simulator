import pytest
from fee_simulator.models.custom_types import (
    FeeDistribution,
    FeeEntry,
    TransactionBudget,
    TransactionRoundResults,
    Round,
    Rotation,
)
from fee_simulator.core.distribute_fees import distribute_fees
from fee_simulator.models.constants import addresses_pool


def initialize_fee_distribution() -> FeeDistribution:
    """Initialize a new fee distribution object."""
    fee_entries = {addr: FeeEntry() for addr in addresses_pool}
    return FeeDistribution(fees=fee_entries)


def compute_total_fees(fee_entry: FeeEntry) -> int:
    """Compute total fees for a FeeEntry, excluding stake."""
    return (
        fee_entry.leader_node
        + fee_entry.validator_node
        + fee_entry.sender_node
        + fee_entry.appealant_node
    )


def test_normal_round():
    """Test fee distribution for a normal round with all validators agreeing."""
    # Setup
    rotation = Rotation(
        votes={
            addresses_pool[0]: ["LeaderReceipt", "Agree"],
            addresses_pool[1]: "Agree",
            addresses_pool[2]: "Agree",
            addresses_pool[3]: "Agree",
            addresses_pool[4]: "Agree",
        }
    )
    round = Round(rotations=[rotation])
    transaction_results = TransactionRoundResults(rounds=[round])
    transaction_budget = TransactionBudget(
        leaderTimeout=100,
        validatorsTimeout=200,
        appealRounds=1,
        rotations=[1],
        senderAddress=addresses_pool[10],
        appeals=[],
        staking_distribution="constant",
    )
    fee_distribution = initialize_fee_distribution()

    # Execute
    result, round_labels = distribute_fees(
        fee_distribution=fee_distribution,
        transaction_results=transaction_results,
        transaction_budget=transaction_budget,
        verbose=False,
    )

    # Assert
    assert round_labels == [
        "normal_round"
    ], f"Expected ['normal_round'], got {round_labels}"
    assert (
        compute_total_fees(result.fees[addresses_pool[0]]) == 300
    ), "Leader should have 100 (leader) + 200 (validator)"
    assert (
        compute_total_fees(result.fees[addresses_pool[1]]) == 200
    ), "Validator should have 200"
    assert (
        compute_total_fees(result.fees[addresses_pool[2]]) == 200
    ), "Validator should have 200"
    assert (
        compute_total_fees(result.fees[addresses_pool[3]]) == 200
    ), "Validator should have 200"
    assert (
        compute_total_fees(result.fees[addresses_pool[4]]) == 200
    ), "Validator should have 200"
    assert (
        compute_total_fees(result.fees[addresses_pool[10]]) == 0
    ), "Sender should have no fees in normal round"

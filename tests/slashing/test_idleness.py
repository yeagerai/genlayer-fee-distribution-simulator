from fee_simulator.models.custom_types import (
    TransactionBudget,
    Rotation,
    Round,
    TransactionRoundResults,
)
from fee_simulator.core.distribute_fees import distribute_fees
from fee_simulator.core.utils import (
    pretty_print_transaction_results,
    pretty_print_fee_distribution,
    initialize_fee_distribution,
)
from fee_simulator.models.constants import addresses_pool


def test_idle_round(default_budget: TransactionBudget, verbose: bool = True):
    """Test fee distribution for a normal round with some validators idle."""
    # Setup
    rotation = Rotation(
        votes={
            addresses_pool[0]: ["LeaderReceipt", "Agree"],  # Leader agrees
            addresses_pool[1]: "Agree",  # Validator 1 agrees
            addresses_pool[2]: "Idle",  # Validator 2 is idle
            addresses_pool[3]: "Agree",  # Validator 3 agrees
            addresses_pool[4]: "Idle",  # Validator 4 is idle
        }
    )
    round = Round(rotations=[rotation])
    transaction_results = TransactionRoundResults(rounds=[round])
    transaction_budget = default_budget
    fee_distribution = initialize_fee_distribution()

    # Execute
    result, round_labels = distribute_fees(
        fee_distribution=fee_distribution,
        transaction_results=transaction_results,
        transaction_budget=transaction_budget,
        verbose=True,  # Set to True to ensure printing
    )

    # Print if verbose
    if verbose:
        pretty_print_transaction_results(transaction_results, round_labels)
        pretty_print_fee_distribution(result)

    # Assertions (adjust based on expected behavior)
    # Example: Check that idle validators receive no fees or are penalized
    assert result.fees[addresses_pool[0]].leader_node > 0, "Leader should receive a fee"
    assert (
        result.fees[addresses_pool[1]].validator_node > 0
    ), "Agree validator should receive a fee"
    assert (
        result.fees[addresses_pool[2]].validator_node == 0
    ), "Idle validator should receive no fee"
    assert (
        result.fees[addresses_pool[3]].validator_node > 0
    ), "Agree validator should receive a fee"
    assert (
        result.fees[addresses_pool[4]].validator_node == 0
    ), "Idle validator should receive no fee"
    assert (
        result.fees[addresses_pool[2]].stake == default_budget.staking_mean
        or result.fees[addresses_pool[2]].stake < default_budget.staking_mean
    ), "Idle validator's stake should be unchanged or slashed"
    assert (
        result.fees[addresses_pool[4]].stake == default_budget.staking_mean
        or result.fees[addresses_pool[4]].stake < default_budget.staking_mean
    ), "Idle validator's stake should be unchanged or slashed"

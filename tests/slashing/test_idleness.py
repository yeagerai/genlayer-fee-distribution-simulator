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
    compute_total_fees,
)
from fee_simulator.models.constants import (
    addresses_pool,
    penalty_reward_coefficient,
    DEFAULT_STAKE,
)


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
        },
        reserve_votes={
            addresses_pool[5]: "Agree",
            addresses_pool[6]: "Disagree",
        },
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
        verbose=False,  # Set to True to ensure printing
    )

    # Print if verbose
    if verbose:
        pretty_print_transaction_results(transaction_results, round_labels)
        pretty_print_fee_distribution(result)

    # Assertions (adjust based on expected behavior)
    # Example: Check that idle validators receive no fees or are penalized
    assert (
        result.fees[addresses_pool[2]].stake == DEFAULT_STAKE * 0.98
    ), "Idle validator's stake should be slashed"
    assert (
        result.fees[addresses_pool[4]].stake == DEFAULT_STAKE * 0.98
    ), "Idle validator's stake should be slashed"

    assert (
        compute_total_fees(result.fees[addresses_pool[0]])
        == default_budget.validatorsTimeout + default_budget.leaderTimeout
    ), " Leader should have 100 (leader) + 200 (validator, no majority)"
    assert (
        compute_total_fees(result.fees[addresses_pool[1]])
        == default_budget.validatorsTimeout
    ), "Validator in majority should have 200"
    assert (
        compute_total_fees(result.fees[addresses_pool[2]]) == 0
    ), "Validator penalized for not being in majority"
    assert (
        compute_total_fees(result.fees[addresses_pool[3]])
        == default_budget.validatorsTimeout
    ), "Validator in majority should have 200"
    assert (
        compute_total_fees(result.fees[addresses_pool[4]]) == 0
    ), "Validator penalized for not being in majority"
    assert (
        compute_total_fees(result.fees[addresses_pool[5]])
        == default_budget.validatorsTimeout
    ), "Validator in majority should have 200"
    assert (
        compute_total_fees(result.fees[addresses_pool[6]])
        == -default_budget.validatorsTimeout * penalty_reward_coefficient
    ), "Validator penalized for not being in majority"

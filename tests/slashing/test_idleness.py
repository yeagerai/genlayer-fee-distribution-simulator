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

leaderTimeout = 100
validatorsTimeout = 200
default_budget = TransactionBudget(
    leaderTimeout=leaderTimeout,
    validatorsTimeout=validatorsTimeout,
    appealRounds=0,
    rotations=[0],
    senderAddress=addresses_pool[1999],
    appeals=[],
    staking_distribution="constant",
)


def test_idle_round(verbose: bool = True):
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

    # Round Label Assert
    assert round_labels == [
        "normal_round"
    ], f"Expected ['normal_round'], got {round_labels}"

    # Assert Stake Slashing
    assert (
        result.fees[addresses_pool[2]].stake == DEFAULT_STAKE * 0.98
    ), "Idle validator's stake should be slashed"
    assert (
        result.fees[addresses_pool[4]].stake == DEFAULT_STAKE * 0.98
    ), "Idle validator's stake should be slashed"

    # Leader Fees Assert
    assert (
        compute_total_fees(result.fees[addresses_pool[0]])
        == validatorsTimeout + leaderTimeout
    ), " Leader should have 100 (leader) + 200 (validator, no majority)"

    # Majority Validator Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == validatorsTimeout
        for i in [1, 3, 5]
    ), "Validator in majority should have 200"

    # Minority Validator Fees Assert
    assert (
        compute_total_fees(result.fees[addresses_pool[6]])
        == -validatorsTimeout * penalty_reward_coefficient
    ), "Validator penalized for not being in majority"

    # Sender Fees Assert
    assert (
        compute_total_fees(result.fees[default_budget.senderAddress])
        == -leaderTimeout - 3 * validatorsTimeout
    ), "Sender should have negative fees equal to the leaderTimeout plus three validatorsTimeout one of them being the leader"

    # Everyone Else 0 Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == 0
        for i in range(len(addresses_pool))
        if i not in [0, 1, 3, 5, 6, 1999]
    ), "Everyone else should have no fees in normal round"

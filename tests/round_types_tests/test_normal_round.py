from fee_simulator.models.custom_types import (
    TransactionRoundResults,
    Round,
    Rotation,
    TransactionBudget,
)
from fee_simulator.core.distribute_fees import distribute_fees
from fee_simulator.models.constants import addresses_pool, penalty_reward_coefficient
from fee_simulator.core.utils import (
    initialize_fee_distribution,
    compute_total_fees,
    compute_total_cost,
)
from fee_simulator.core.display import (
    pretty_print_fee_distribution,
    pretty_print_transaction_results,
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


def test_normal_round(verbose):
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
    transaction_budget = default_budget
    fee_distribution = initialize_fee_distribution()

    # Execute
    result, round_labels = distribute_fees(
        fee_distribution=fee_distribution,
        transaction_results=transaction_results,
        transaction_budget=transaction_budget,
    )

    # Print if verbose
    if verbose:
        pretty_print_transaction_results(transaction_results, round_labels)
        pretty_print_fee_distribution(result)

    # Round Label Assert
    assert round_labels == [
        "normal_round"
    ], f"Expected ['normal_round'], got {round_labels}"

    # Leader Fees Assert
    assert (
        compute_total_fees(result.fees[addresses_pool[0]])
        == leaderTimeout + validatorsTimeout
    ), "Leader should have 100 (leader) + 200 (validator)"

    # Validator Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == validatorsTimeout
        for i in [1, 2, 3, 4]
    ), "Validator should have 200"

    # Sender Fees Assert
    assert compute_total_fees(
        result.fees[default_budget.senderAddress]
    ) == -compute_total_cost(
        default_budget
    ), "Sender should have negative fees equal to the total cost of the transaction in normal round"

    # Everyone Else 0 Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == 0
        for i in range(len(addresses_pool))
        if i not in [0, 1, 2, 3, 4, 1999]
    ), "Everyone else should have no fees in normal round"


def test_normal_round_with_minority_penalties(verbose):
    """Test normal round with penalties for validators in the minority (3 Agree, 1 Disagree, 1 Timeout)."""
    # Setup
    rotation = Rotation(
        votes={
            addresses_pool[0]: ["LeaderReceipt", "Agree"],  # Majority
            addresses_pool[1]: "Agree",  # Majority
            addresses_pool[2]: "Agree",  # Majority
            addresses_pool[3]: "Disagree",  # Minority
            addresses_pool[4]: "Timeout",  # Minority
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
    )

    # Print if verbose
    if verbose:
        pretty_print_transaction_results(transaction_results, round_labels)
        pretty_print_fee_distribution(result)

    # Round Label Assert
    assert round_labels == [
        "normal_round"
    ], f"Expected ['normal_round'], got {round_labels}"

    # Leader Fees Assert
    assert (
        compute_total_fees(result.fees[addresses_pool[0]])
        == leaderTimeout + validatorsTimeout
    ), "Leader should have 100 (leader) + 200 (validator)"

    # Majority Validator Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == validatorsTimeout
        for i in [1, 2]
    ), "Validator in majority should have 200"

    # Minority Validator Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]])
        == -penalty_reward_coefficient * validatorsTimeout
        for i in [3, 4]
    ), "Validator in minority should have 200"

    # Sender Fees Assert
    assert (
        compute_total_fees(result.fees[default_budget.senderAddress])
        == -leaderTimeout - validatorsTimeout
    ), "Sender should have negative fees equal to the leaderTimeout as the two negative validators fees cancel out the positive ones so only the leader fee is left"

    # Everyone Else 0 Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == 0
        for i in range(len(addresses_pool))
        if i not in [0, 1, 2, 3, 4, 1999]
    ), "Everyone else should have no fees in normal round"


def test_normal_round_no_majority(verbose):
    """Test normal round with no majority (2 Agree, 2 Disagree, 1 Timeout)."""
    # Setup
    rotation = Rotation(
        votes={
            addresses_pool[0]: ["LeaderReceipt", "Agree"],  # No majority
            addresses_pool[1]: "Agree",  # No majority
            addresses_pool[2]: "Disagree",  # No majority
            addresses_pool[3]: "Disagree",  # No majority
            addresses_pool[4]: "Timeout",  # No majority
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
    )

    # Print if verbose
    if verbose:
        pretty_print_transaction_results(transaction_results, round_labels)
        pretty_print_fee_distribution(result)

    # Round Label Assert
    assert round_labels == [
        "normal_round"
    ], f"Expected ['normal_round'], got {round_labels}"

    # Leader Fees Assert
    assert (
        compute_total_fees(result.fees[addresses_pool[0]])
        == leaderTimeout + validatorsTimeout
    ), "Leader should have 100 (leader) + 200 (validator)"

    # Validator Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == validatorsTimeout
        for i in [1, 2, 3, 4]
    ), "Validator should have 200"

    # Sender Fees Assert
    assert compute_total_fees(
        result.fees[default_budget.senderAddress]
    ) == -compute_total_cost(
        default_budget
    ), "Sender should have negative fees equal to the total cost of the transaction in normal round"

    # Everyone Else 0 Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == 0
        for i in range(len(addresses_pool))
        if i not in [0, 1, 2, 3, 4, 1999]
    ), "Everyone else should have no fees in normal round"


def test_normal_round_no_majority_disagree(verbose):
    """Test normal round with no majority (2 Agree, 2 Disagree, 1 Timeout)."""
    # Setup
    rotation = Rotation(
        votes={
            addresses_pool[0]: ["LeaderReceipt", "Agree"],  # No majority
            addresses_pool[1]: "Agree",  # No majority
            addresses_pool[2]: "Disagree",  # No majority
            addresses_pool[3]: "Disagree",  # No majority
            addresses_pool[4]: "Disagree",  # No majority
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
    )

    # Print if verbose
    if verbose:
        pretty_print_transaction_results(transaction_results, round_labels)
        pretty_print_fee_distribution(result)

    # Round Label Assert
    assert round_labels == [
        "normal_round"
    ], f"Expected ['normal_round'], got {round_labels}"

    # Leader Fees Assert
    assert (
        compute_total_fees(result.fees[addresses_pool[0]])
        == leaderTimeout + validatorsTimeout
    ), "Leader should have 100 (leader) + 200 (validator)"

    # Validator Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == validatorsTimeout
        for i in [1, 2, 3, 4]
    ), "Validator should have 200"

    # Sender Fees Assert
    assert compute_total_fees(
        result.fees[default_budget.senderAddress]
    ) == -compute_total_cost(
        default_budget
    ), "Sender should have negative fees equal to the total cost of the transaction in normal round"

    # Everyone Else 0 Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == 0
        for i in range(len(addresses_pool))
        if i not in [0, 1, 2, 3, 4, 1999]
    ), "Everyone else should have no fees in normal round"

from fee_simulator.models.custom_types import (
    TransactionRoundResults,
    Round,
    Rotation,
)
from fee_simulator.core.distribute_fees import distribute_fees
from fee_simulator.models.constants import addresses_pool, penalty_reward_coefficient
from fee_simulator.core.utils import (
    initialize_fee_distribution,
    compute_total_fees,
    pretty_print_transaction_results,
    pretty_print_fee_distribution,
)


def test_normal_round(default_budget, verbose):
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
        verbose=False,
    )

    # Print if verbose
    if verbose:
        pretty_print_transaction_results(transaction_results, round_labels)
        pretty_print_fee_distribution(result)

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
        compute_total_fees(result.fees[addresses_pool[10]])
        == 0  # Maybe this should be -1100 ?
    ), "Sender should have no fees in normal round"

    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == 0
        for i in range(len(addresses_pool))
        if i not in [0, 1, 2, 3, 4, 10]
    ), "Everyone else should have no fees in normal round"


def test_normal_round_with_minority_penalties(default_budget, verbose):
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
        verbose=False,
    )

    # Print if verbose
    if verbose:
        pretty_print_transaction_results(transaction_results, round_labels)
        pretty_print_fee_distribution(result)

    # Assert
    assert round_labels == [
        "normal_round"
    ], f"Expected ['normal_round'], got {round_labels}"
    assert (
        compute_total_fees(result.fees[addresses_pool[0]])
        == default_budget.leaderTimeout + default_budget.validatorsTimeout
    ), "Leader should have 100 (leader) + 200 (validator)"
    assert (
        compute_total_fees(result.fees[addresses_pool[1]])
        == default_budget.validatorsTimeout
    ), "Validator in majority should have 200"
    assert (
        compute_total_fees(result.fees[addresses_pool[2]])
        == default_budget.validatorsTimeout
    ), "Validator in majority should have 200"
    assert (
        compute_total_fees(result.fees[addresses_pool[3]])
        == -default_budget.validatorsTimeout * penalty_reward_coefficient
    ), "Validator in minority (Disagree) should lose 2 * 200"
    assert (
        compute_total_fees(result.fees[addresses_pool[4]])
        == -default_budget.validatorsTimeout * penalty_reward_coefficient
    ), "Validator in minority (Timeout) should lose 2 * 200"
    assert (
        compute_total_fees(result.fees[addresses_pool[10]]) == 0
    ), "Sender should have no fees in normal round"

    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == 0
        for i in range(len(addresses_pool))
        if i not in [0, 1, 2, 3, 4, 10]
    ), "Everyone else should have no fees in normal round"


def test_normal_round_no_majority(default_budget, verbose):
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
        verbose=False,
    )

    # Print if verbose
    if verbose:
        pretty_print_transaction_results(transaction_results, round_labels)
        pretty_print_fee_distribution(result)

    # Assert
    assert round_labels == [
        "normal_round"
    ], f"Expected ['normal_round'], got {round_labels}"
    assert (
        compute_total_fees(result.fees[addresses_pool[0]])
        == default_budget.validatorsTimeout + default_budget.leaderTimeout
    ), " Leader should have 100 (leader) + 200 (validator, no majority)"
    assert (
        compute_total_fees(result.fees[addresses_pool[1]])
        == default_budget.validatorsTimeout
    ), "Validator should have 200 (no majority, no penalty)"
    assert (
        compute_total_fees(result.fees[addresses_pool[2]])
        == default_budget.validatorsTimeout
    ), "Validator should have 200 (no majority, no penalty)"
    assert (
        compute_total_fees(result.fees[addresses_pool[3]])
        == default_budget.validatorsTimeout
    ), "Validator should have 200 (no majority, no penalty)"
    assert (
        compute_total_fees(result.fees[addresses_pool[4]])
        == default_budget.validatorsTimeout
    ), "Validator should have 200 (no majority, no penalty)"
    assert (
        compute_total_fees(result.fees[addresses_pool[10]]) == 0
    ), "Sender should have no fees in normal round"

    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == 0
        for i in range(len(addresses_pool))
        if i not in [0, 1, 2, 3, 4, 10]
    ), "Everyone else should have no fees in normal round"


def test_normal_round_no_majority_disagree(default_budget, verbose):
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
        verbose=False,
    )

    # Print if verbose
    if verbose:
        pretty_print_transaction_results(transaction_results, round_labels)
        pretty_print_fee_distribution(result)

    # Assert
    assert round_labels == [
        "normal_round"
    ], f"Expected ['normal_round'], got {round_labels}"
    assert (
        compute_total_fees(result.fees[addresses_pool[0]])
        == default_budget.validatorsTimeout + default_budget.leaderTimeout
    ), " Leader should have 100 (leader) + 200 (validator, no majority)"
    assert (
        compute_total_fees(result.fees[addresses_pool[1]])
        == default_budget.validatorsTimeout
    ), "Validator should have 200 (no majority, no penalty)"
    assert (
        compute_total_fees(result.fees[addresses_pool[2]])
        == default_budget.validatorsTimeout
    ), "Validator should have 200 (no majority, no penalty)"
    assert (
        compute_total_fees(result.fees[addresses_pool[3]])
        == default_budget.validatorsTimeout
    ), "Validator should have 200 (no majority, no penalty)"
    assert (
        compute_total_fees(result.fees[addresses_pool[4]])
        == default_budget.validatorsTimeout
    ), "Validator should have 200 (no majority, no penalty)"
    assert (
        compute_total_fees(result.fees[addresses_pool[10]]) == 0
    ), "Sender should have no fees in normal round"

    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == 0
        for i in range(len(addresses_pool))
        if i not in [0, 1, 2, 3, 4, 10]
    ), "Everyone else should have no fees in normal round"

# leader timeout
# appeal
# normal round
# el nuevo leader cobra un 150% del timeout

import pytest
from fee_simulator.models.custom_types import (
    TransactionRoundResults,
    Round,
    Rotation,
    Appeal,
    TransactionBudget,
)
from fee_simulator.core.distribute_fees import distribute_fees
from fee_simulator.models.constants import addresses_pool
from fee_simulator.core.utils import (
    initialize_fee_distribution,
    compute_total_fees,
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
    appealRounds=1,
    rotations=[0, 0],
    senderAddress=addresses_pool[1999],
    appeals=[],
    staking_distribution="constant",
)


def test_appeal_leader_timeout_150_previous_normal_round(verbose):
    """Test appeal_leader_timeout_150_previous_normal_round: normal round (undetermined), appeal successful, normal round."""
    # Setup
    # First round: 5 validators, undetermined (2 Agree, 2 Disagree, 1 Timeout)
    rotation1 = Rotation(
        votes={
            addresses_pool[0]: ["LeaderTimeout", "NA"],
            addresses_pool[1]: "NA",
            addresses_pool[2]: "NA",
            addresses_pool[3]: "NA",
            addresses_pool[4]: "NA",
        }
    )
    # Second round (appeal): 7 validators, majority Agree
    rotation2 = Rotation(
        votes={addresses_pool[i]: "NA" for i in [5, 6, 7, 8, 9, 10, 11]}
    )

    # Third round: 11 validators, majority Agree
    rotation3 = Rotation(
        votes={
            addresses_pool[5]: ["LeaderReceipt", "Agree"],
            addresses_pool[2]: "Agree",
            addresses_pool[3]: "Agree",
            addresses_pool[4]: "Agree",
            addresses_pool[1]: "Agree",
            addresses_pool[6]: "Agree",
            addresses_pool[7]: "Disagree",
            addresses_pool[8]: "Disagree",
            addresses_pool[9]: "Disagree",
            addresses_pool[10]: "Timeout",
            addresses_pool[11]: "Timeout",
        }
    )
    transaction_results = TransactionRoundResults(
        rounds=[
            Round(rotations=[rotation1]),
            Round(rotations=[rotation2]),
            Round(rotations=[rotation3]),
        ]
    )
    transaction_budget = default_budget
    transaction_budget.appeals = [Appeal(appealantAddress=addresses_pool[23])]
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
        "skip_round",
        "appeal_leader_timeout_successful",
        "leader_timeout_150_previous_normal_round",
    ], f"Expected ['skip_round', 'appeal_leader_timeout_successful', 'leader_timeout_150_previous_normal_round'], got {round_labels}"

    # Everyone Else 0 Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == 0
        for i in range(len(addresses_pool))
        if i not in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 23, 1999]
    ), "Everyone else should have no fees in normal round"

    # Appealant Fees Assert
    assert (
        compute_total_fees(result.fees[addresses_pool[23]]) == leaderTimeout
    ), "Appealant should have fees equal to the leaderTimeout as the appeal was successful"

    # 1st Leader Fees Assert
    assert (
        compute_total_fees(result.fees[addresses_pool[0]]) == 0
    ), "1st Leader should have fees equal to the leaderTimeout"

    # 2nd Leader Fees Assert
    assert (
        compute_total_fees(result.fees[addresses_pool[5]])
        == leaderTimeout + validatorsTimeout
    ), "2nd Leader should have fees equal to the leaderTimeout"

    # Winner Validator Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == validatorsTimeout
        for i in [2, 3, 4, 6]
    ), "Winner Validator should have fees equal to the validatorsTimeout"

    # Loser Validator Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == -validatorsTimeout
        for i in [7, 8, 9, 10, 11]
    ), "Loser Validator should have no fees"

    # Sender Fees Assert
    assert (
        compute_total_fees(result.fees[default_budget.senderAddress])
        == -2 * leaderTimeout - validatorsTimeout
    ), "Sender should have negative fees equal to the two times leaderTimeout (one leader, and one bonus for appealant) and one validatorsTimeout as the rest cancel out"

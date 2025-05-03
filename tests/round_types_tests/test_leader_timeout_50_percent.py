# leader hace timeout y cobra un 50% del timeout
# validadores no responden nada y ni cobran ni pagan nada, por tanto el resto del mundo a 0
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


def test_leader_timeout_50_percent(verbose):
    """Test fee distribution for a leader timeout round."""
    # Setup
    rotation = Rotation(
        votes={
            addresses_pool[0]: ["LeaderTimeout", "NA"],
            addresses_pool[1]: "NA",
            addresses_pool[2]: "NA",
            addresses_pool[3]: "NA",
            addresses_pool[4]: "NA",
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
        "leader_timeout_50_percent"
    ], f"Expected ['leader_timeout_50_percent'], got {round_labels}"

    # Leader Fees Assert
    assert (
        compute_total_fees(result.fees[addresses_pool[0]])
        == leaderTimeout * 0.5
    ), "Leader should have 100 (leader) * 0.5 (50%)"

    # Everyone Else 0 Fees Assert
    assert all(
        compute_total_fees(result.fees[addresses_pool[i]]) == 0
        for i in range(len(addresses_pool))
        if i not in [0, 1999]
    ), "Everyone else should have no fees in normal round"

    # Sender Fees Assert
    assert compute_total_fees(
        result.fees[default_budget.senderAddress]
    ) == -leaderTimeout*0.5, "Sender should have negative fees equal to the total cost of the transaction in normal round"
    # TODO: should the sender be refunded with everything but the 50 percent of the leader timeout?
    # is the current situation
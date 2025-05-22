import pytest
import itertools
from fee_simulator.models import (
    TransactionRoundResults,
    Round,
    Rotation,
    TransactionBudget,
)
from fee_simulator.core.transaction_processing import process_transaction
from fee_simulator.utils import compute_total_cost, generate_random_eth_address
from fee_simulator.fee_aggregators.address_metrics import (
    compute_total_earnings,
    compute_total_costs,
    compute_total_burnt,
)
from fee_simulator.constants import PENALTY_REWARD_COEFFICIENT
from fee_simulator.display import (
    display_transaction_results,
    display_fee_distribution,
    display_summary_table,
    display_test_description,
)
from tests.invariant_checks import check_invariants

# Constants
LEADER_TIMEOUT = 100
VALIDATORS_TIMEOUT = 200
NUM_VALIDATORS = 4  # Plus 1 leader, total 5 participants per ROUND_SIZES[0]
VOTE_TYPES = ["AGREE", "DISAGREE", "TIMEOUT"]

# Generate addresses
addresses_pool = [generate_random_eth_address() for _ in range(2000)]
sender_address = addresses_pool[1999]

# Transaction budget (no appeals, single round)
transaction_budget = TransactionBudget(
    leaderTimeout=LEADER_TIMEOUT,
    validatorsTimeout=VALIDATORS_TIMEOUT,
    appealRounds=0,
    rotations=[0],
    senderAddress=sender_address,
    appeals=[],
    staking_distribution="constant",
)


@pytest.mark.parametrize(
    "leader_action,votes",
    [
        (leader_action, votes)
        for leader_action in ["LEADER_RECEIPT", "LEADER_TIMEOUT"]
        for votes in itertools.product(VOTE_TYPES, repeat=NUM_VALIDATORS)
    ],
    ids=lambda x: (
        f"leader_{x[0]}_votes_{'-'.join(x[1])}" if isinstance(x, tuple) else str(x)
    ),
)
def test_combinatorial_round(verbose, debug, leader_action, votes):
    """
    Combinatorial test for a single round with all validator vote combinations and leader actions.
    Tests fee distribution, round labeling, and invariants.
    """
    # Setup test description
    vote_str = ", ".join(f"Validator {i+1}: {vote}" for i, vote in enumerate(votes))
    test_description = (
        f"This test verifies the fee distribution for a single round with leader action '{leader_action}' "
        f"and validator votes: {vote_str}. It checks that the simulator correctly labels the round, "
        f"distributes fees according to the majority outcome, penalizes minority validators if applicable, "
        f"and satisfies all invariants (costs equal earnings, no free burns, party safety)."
    )

    # Print test description if verbose
    if verbose:
        display_test_description(
            test_name=f"test_combinatorial_{leader_action}_{'-'.join(votes)}",
            test_description=test_description,
        )

    # Setup rotation
    rotation_votes = {
        addresses_pool[0]: [
            leader_action,
            "AGREE" if leader_action == "LEADER_RECEIPT" else "NA",
        ],
    }
    for i, vote in enumerate(votes):
        rotation_votes[addresses_pool[i + 1]] = vote

    rotation = Rotation(votes=rotation_votes, reserve_votes={})
    round = Round(rotations=[rotation])
    transaction_results = TransactionRoundResults(rounds=[round])

    # Execute transaction processing
    fee_events, round_labels = process_transaction(
        addresses=addresses_pool,
        transaction_results=transaction_results,
        transaction_budget=transaction_budget,
    )

    # Print results if verbose or debug
    if verbose:
        display_summary_table(
            fee_events, transaction_results, transaction_budget, round_labels
        )
        display_transaction_results(transaction_results, round_labels)
    if debug:
        display_fee_distribution(fee_events)

    # Invariant checks
    check_invariants(fee_events, transaction_budget, transaction_results)

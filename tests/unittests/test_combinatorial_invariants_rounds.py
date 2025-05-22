import pytest
import itertools
from fee_simulator.models import (
    TransactionRoundResults,
    Round,
    Rotation,
    TransactionBudget,
    Appeal,
)
from fee_simulator.core.transaction_processing import process_transaction
from fee_simulator.utils import compute_total_cost, generate_random_eth_address
from fee_simulator.fee_aggregators.address_metrics import (
    compute_total_earnings,
    compute_total_costs,
    compute_total_burnt,
)
from fee_simulator.constants import PENALTY_REWARD_COEFFICIENT, ROUND_SIZES
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
VOTE_TYPES = ["AGREE", "DISAGREE", "TIMEOUT"]
LEADER_ACTIONS = ["LEADER_RECEIPT", "LEADER_TIMEOUT"]

# Generate addresses
addresses_pool = [generate_random_eth_address() for _ in range(2000)]
sender_address = addresses_pool[1999]
appealant_address = addresses_pool[1998]

# Transaction budgets for different round counts
BUDGETS = {
    1: TransactionBudget(
        leaderTimeout=LEADER_TIMEOUT,
        validatorsTimeout=VALIDATORS_TIMEOUT,
        appealRounds=0,
        rotations=[0],
        senderAddress=sender_address,
        appeals=[],
        staking_distribution="constant",
    ),
    2: TransactionBudget(
        leaderTimeout=LEADER_TIMEOUT,
        validatorsTimeout=VALIDATORS_TIMEOUT,
        appealRounds=1,
        rotations=[0, 0],
        senderAddress=sender_address,
        appeals=[Appeal(appealantAddress=appealant_address)],
        staking_distribution="constant",
    ),
    3: TransactionBudget(
        leaderTimeout=LEADER_TIMEOUT,
        validatorsTimeout=VALIDATORS_TIMEOUT,
        appealRounds=2,
        rotations=[0, 0, 0],
        senderAddress=sender_address,
        appeals=[
            Appeal(appealantAddress=appealant_address),
            Appeal(appealantAddress=appealant_address),
        ],
        staking_distribution="constant",
    ),
}


VOTE_CONFIGS = {
    0: get_vote_configs(4),  # Round 0: 5 participants (4 validators + 1 leader)
    1: get_vote_configs(6),  # Round 1: 7 participants (6 validators + 1 leader)
    2: get_vote_configs(10),  # Round 2: 11 participants (10 validators + 1 leader)
}


def create_rotation(leader_action, votes, round_index, address_offset):
    """Create a Rotation object for a given round."""
    num_validators = ROUND_SIZES[round_index] - 1  # Subtract 1 for leader
    rotation_votes = {
        addresses_pool[address_offset]: [
            leader_action,
            "AGREE" if leader_action == "LEADER_RECEIPT" else "NA",
        ],
    }
    for i in range(num_validators):
        vote = votes[i] if round_index % 2 == 0 and i < len(votes) else "NA"
        rotation_votes[addresses_pool[address_offset + i + 1]] = vote
    return Rotation(votes=rotation_votes, reserve_votes={})


@pytest.mark.parametrize(
    "leader_action,votes",
    [
        (leader_action, votes)
        for leader_action, votes in itertools.product(LEADER_ACTIONS, VOTE_CONFIGS[0])
    ],
    ids=lambda x: (
        f"leader_{x[0]}_votes_{'-'.join(x[1])}" if isinstance(x, tuple) else str(x)
    ),
)
def test_combinatorial_1_round(verbose, debug, leader_action, votes):
    """
    Combinatorial test for a single round with representative vote combinations and leader actions.
    """
    vote_str = ", ".join(f"Validator {i+1}: {vote}" for i, vote in enumerate(votes))
    test_description = (
        f"Single round test with leader action '{leader_action}', votes: {vote_str}. "
        f"Verifies round labeling, fee distribution, and invariants."
    )

    if verbose:
        display_test_description(
            test_name=f"test_1_round_{leader_action}_{'-'.join(votes)}",
            test_description=test_description,
        )

    rotation = create_rotation(leader_action, votes, round_index=0, address_offset=0)
    transaction_results = TransactionRoundResults(rounds=[Round(rotations=[rotation])])
    transaction_budget = BUDGETS[1]

    fee_events, round_labels = process_transaction(
        addresses=addresses_pool,
        transaction_results=transaction_results,
        transaction_budget=transaction_budget,
    )

    if verbose:
        display_summary_table(
            fee_events, transaction_results, transaction_budget, round_labels
        )
        display_transaction_results(transaction_results, round_labels)
    if debug:
        display_fee_distribution(fee_events)

    check_invariants(fee_events, transaction_budget, transaction_results)


@pytest.mark.parametrize(
    "round1_leader,round1_votes,round2_leader",
    [
        (r1_leader, r1_votes, r2_leader)
        for r1_leader, r1_votes, r2_leader in itertools.product(
            LEADER_ACTIONS, VOTE_CONFIGS[0], LEADER_ACTIONS
        )
    ],
    ids=lambda x: (
        f"r1_leader_{x[0]}_r1_votes_{'-'.join(x[1])}_r2_leader_{x[2]}"
        if isinstance(x, tuple)
        else str(x)
    ),
)
def test_combinatorial_2_rounds(
    verbose, debug, round1_leader, round1_votes, round2_leader
):
    """
    Combinatorial test for two rounds with representative vote combinations and leader actions.
    """
    vote_str1 = ", ".join(
        f"Validator {i+1}: {vote}" for i, vote in enumerate(round1_votes)
    )
    test_description = (
        f"Two-round test with Round 1 leader action '{round1_leader}', votes: {vote_str1}; "
        f"Round 2 leader action '{round2_leader}'. Verifies round labeling, fee distribution, and invariants."
    )

    if verbose:
        display_test_description(
            test_name=f"test_2_rounds_{round1_leader}_{'-'.join(round1_votes)}_{round2_leader}",
            test_description=test_description,
        )

    rotation1 = create_rotation(
        round1_leader, round1_votes, round_index=0, address_offset=0
    )
    rotation2 = create_rotation(
        round2_leader, [], round_index=1, address_offset=5
    )  # Appeal round, votes are NA
    transaction_results = TransactionRoundResults(
        rounds=[Round(rotations=[rotation1]), Round(rotations=[rotation2])]
    )
    transaction_budget = BUDGETS[2]

    fee_events, round_labels = process_transaction(
        addresses=addresses_pool,
        transaction_results=transaction_results,
        transaction_budget=transaction_budget,
    )

    if verbose:
        display_summary_table(
            fee_events, transaction_results, transaction_budget, round_labels
        )
        display_transaction_results(transaction_results, round_labels)
    if debug:
        display_fee_distribution(fee_events)

    check_invariants(fee_events, transaction_budget, transaction_results)


@pytest.mark.parametrize(
    "round1_leader,round1_votes,round2_leader,round3_leader,round3_votes",
    [
        (r1_leader, r1_votes, r2_leader, r3_leader, r3_votes)
        for r1_leader, r1_votes, r2_leader, r3_leader, r3_votes in itertools.islice(
            itertools.product(
                LEADER_ACTIONS,
                VOTE_CONFIGS[0],
                LEADER_ACTIONS,
                LEADER_ACTIONS,
                VOTE_CONFIGS[2],
            ),
            32,
        )
    ],
    ids=lambda x: (
        f"r1_leader_{x[0]}_r1_votes_{'-'.join(x[1])}_r2_leader_{x[2]}_r3_leader_{x[3]}_r3_votes_{'-'.join(x[4])}"
        if isinstance(x, tuple)
        else str(x)
    ),
)
def test_combinatorial_3_rounds(
    verbose,
    debug,
    round1_leader,
    round1_votes,
    round2_leader,
    round3_leader,
    round3_votes,
):
    """
    Combinatorial test for three rounds with a subset of vote combinations and leader actions.
    """
    vote_str1 = ", ".join(
        f"Validator {i+1}: {vote}" for i, vote in enumerate(round1_votes)
    )
    vote_str3 = ", ".join(
        f"Validator {i+1}: {vote}" for i, vote in enumerate(round3_votes)
    )
    test_description = (
        f"Three-round test with Round 1 leader action '{round1_leader}', votes: {vote_str1}; "
        f"Round 2 leader action '{round2_leader}'; Round 3 leader action '{round3_leader}', votes: {vote_str3}. "
        f"Verifies round labeling, fee distribution, and invariants."
    )

    if verbose:
        display_test_description(
            test_name=f"test_3_rounds_{round1_leader}_{'-'.join(round1_votes)}_{round2_leader}_{round3_leader}_{'-'.join(round3_votes)}",
            test_description=test_description,
        )

    rotation1 = create_rotation(
        round1_leader, round1_votes, round_index=0, address_offset=0
    )
    rotation2 = create_rotation(round2_leader, [], round_index=1, address_offset=5)
    rotation3 = create_rotation(
        round3_leader, round3_votes, round_index=2, address_offset=12
    )
    transaction_results = TransactionRoundResults(
        rounds=[
            Round(rotations=[rotation1]),
            Round(rotations=[rotation2]),
            Round(rotations=[rotation3]),
        ]
    )
    transaction_budget = BUDGETS[3]

    fee_events, round_labels = process_transaction(
        addresses=addresses_pool,
        transaction_results=transaction_results,
        transaction_budget=transaction_budget,
    )

    if verbose:
        display_summary_table(
            fee_events, transaction_results, transaction_budget, round_labels
        )
        display_transaction_results(transaction_results, round_labels)
    if debug:
        display_fee_distribution(fee_events)

    check_invariants(fee_events, transaction_budget, transaction_results)

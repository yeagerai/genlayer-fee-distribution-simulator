"""
Combinatorial Fee Distribution Testing

This module uses combinatorial testing to systematically test
fee distribution across all possible combinations of factors.
"""

import itertools
import random
from typing import Dict, List, Tuple
from custom_types import (
    FeeDistribution,
    FeeEntry,
    TransactionBudget,
    TransactionRoundResults,
    Round,
    Rotation,
    Appeal,
    VoteType,
)
from distribute_fees import distribute_fees
from constants import addresses_pool
from utils import (
    pretty_print_fee_distribution,
    pretty_print_transaction_results,
    Colors,
)


def initialize_fee_distribution() -> FeeDistribution:
    """Initialize a new fee distribution object"""
    fee_entries = {}
    for addr in addresses_pool:
        fee_entries[addr] = FeeEntry(
            leader=0,
            leader_node=0,
            validator_node=0,
            sender=0,
            sender_node=0,
            appealant=0,
            appealant_node=0,
        )
    return FeeDistribution(fees=fee_entries)


def generate_vote_combinations(
    committee_size: int, limit_combinations: bool = True
) -> List[Dict[str, str]]:
    """
    Generate all possible vote combinations for a committee

    Args:
        committee_size: Number of validators
        limit_combinations: If True, use equivalence classes to reduce combinations

    Returns:
        List of vote dictionaries
    """
    # Only include valid vote types defined in VoteType
    vote_options = [
        "Agree",
        "Disagree",
        "Timeout",
        "Idle",
    ]  # Added "Idle" as it's now in VoteType

    if limit_combinations:
        # Use equivalence classes: focus on proportions rather than all permutations
        # This drastically reduces the number of combinations

        # For a committee of size n, we care about x validators agreeing, y disagreeing, etc.
        # Generate all possible distributions that sum to committee_size
        distributions = []
        for agree in range(committee_size + 1):
            for disagree in range(committee_size + 1 - agree):
                # The rest are timeout (we only have 3 vote types now)
                timeout = committee_size - agree - disagree
                distributions.append((agree, disagree, timeout))
    else:
        # Full combinatorial explosion - this will be huge!
        all_vote_patterns = list(itertools.product(vote_options, repeat=committee_size))
        return all_vote_patterns  # Warning: this will be 3^committee_size patterns!

    # Convert distributions to vote dictionaries
    vote_dictionaries = []
    for dist in distributions:
        votes = {}
        addr_index = 0

        # Add each type of vote according to distribution
        for vote_type_index, count in enumerate(dist):
            vote_type = vote_options[vote_type_index]
            for _ in range(count):
                # Randomly add a hash (50% chance)
                if random.random() < 0.5:
                    hash_value = "0x" + "".join(
                        random.choices("0123456789abcdef", k=40)
                    )
                    votes[addresses_pool[addr_index]] = [vote_type, hash_value]
                else:
                    votes[addresses_pool[addr_index]] = vote_type
                addr_index += 1

        # Add LeaderReceipt to the first address (if any exist)
        if votes:
            first_addr = next(iter(votes.keys()))
            leader_vote = votes[first_addr]
            if isinstance(leader_vote, list):
                votes[first_addr] = ["LeaderReceipt"] + leader_vote
            else:
                # Randomly add a hash to leader vote
                if random.random() < 0.5:
                    hash_value = "0x" + "".join(
                        random.choices("0123456789abcdef", k=40)
                    )
                    votes[first_addr] = ["LeaderReceipt", leader_vote, hash_value]
                else:
                    votes[first_addr] = ["LeaderReceipt", leader_vote]

        vote_dictionaries.append(votes)

    return vote_dictionaries


def generate_combinatorial_scenarios(
    committee_sizes: List[int], max_rounds: int, max_scenarios: int
) -> List[Tuple[TransactionBudget, TransactionRoundResults]]:
    """
    Generate combinatorial test scenarios

    Args:
        committee_sizes: List of committee sizes to test
        max_rounds: Maximum number of rounds per scenario
        max_scenarios: Maximum number of scenarios to generate

    Returns:
        List of (budget, results) tuples
    """
    scenarios = []

    for size in committee_sizes:
        for num_rounds in range(1, max_rounds + 1):
            vote_combinations = generate_vote_combinations(
                size, limit_combinations=True
            )
            round_combinations = generate_round_combinations(
                vote_combinations, num_rounds
            )

            # Generate only a subset if there are too many combinations
            if len(round_combinations) > sub_limit:
                sampled_combinations = random.sample(round_combinations, sub_limit)
            else:
                sampled_combinations = round_combinations

            for round_votes in sampled_combinations:
                # Create a transaction with these rounds
                rounds = []
                for votes in round_votes:
                    rotation = Rotation(votes=votes)
                    round = Round(rotations=[rotation])
                    rounds.append(round)

                # Add appeals if there are more than 1 round
                appeals = []
                if num_rounds > 1:
                    for i in range(num_rounds - 1):
                        appeal = Appeal(appealantAddress=addresses_pool[i + 200])
                        appeals.append(appeal)

                # Randomly decide staking distribution
                staking_dist = random.choice(["constant", "normal"])

                transaction_budget = TransactionBudget(
                    leaderTimeout=100,
                    validatorsTimeout=200,
                    appealRounds=num_rounds,
                    rotations=[1] * num_rounds,
                    senderAddress=addresses_pool[100],
                    appeals=appeals,
                    staking_distribution=staking_dist,
                    staking_mean=1000 if staking_dist == "normal" else None,
                    staking_variance=100 if staking_dist == "normal" else None,
                )

                transaction_results = TransactionRoundResults(rounds=rounds)
                scenarios.append((transaction_budget, transaction_results))

                if len(scenarios) >= max_scenarios:
                    return scenarios

    return scenarios


def run_combinatorial_tests(
    committee_sizes: List[int] = [3],  # Using small sizes to avoid explosion
    max_rounds: int = 2,
    limit_combinations: bool = True,
    max_scenarios: int = 100,  # Limit to avoid running millions of tests
):
    """
    Run combinatorial tests with different scenarios

    Args:
        committee_sizes: Committee sizes to test
        max_rounds: Maximum number of rounds
        limit_combinations: Whether to use equivalence classes
        max_scenarios: Maximum number of scenarios to test
    """
    print(
        f"\n{Colors.BOLD}{Colors.HEADER}===== COMBINATORIAL FEE DISTRIBUTION TESTS ====={Colors.ENDC}"
    )

    # Generate scenarios
    scenarios = generate_combinatorial_scenarios(
        committee_sizes, max_rounds, max_scenarios
    )

    # Determine number of scenarios to run
    actual_scenarios = min(len(scenarios), max_scenarios)

    print(
        f"{Colors.YELLOW}(Running {actual_scenarios} out of {len(scenarios)} possible combinations){Colors.ENDC}"
    )

    # Run tests
    for i, (transaction_budget, transaction_results) in enumerate(
        scenarios[:actual_scenarios]
    ):
        # Calculate total number of votes for this scenario
        total_votes = sum(
            len(round_obj.rotations[0].votes)
            for round_obj in transaction_results.rounds
        )

        print(
            f"\n{Colors.BOLD}{Colors.GREEN}=== COMBINATION {i+1}/{actual_scenarios}: {len(transaction_results.rounds)} ROUNDS, {total_votes} VOTES ==={Colors.ENDC}"
        )

        # Initialize fee distribution
        fee_distribution = initialize_fee_distribution()

        # Distribute fees
        result, round_labels = distribute_fees(
            fee_distribution=fee_distribution,
            transaction_results=transaction_results,
            transaction_budget=transaction_budget,
            verbose=False,
        )

        # Show transaction structure with round labels
        pretty_print_transaction_results(transaction_results, round_labels)

        # Print fee distribution
        pretty_print_fee_distribution(result.model_dump()["fees"])

    print(
        f"\n{Colors.BOLD}{Colors.GREEN}===== ALL COMBINATORIAL TESTS COMPLETED ====={Colors.ENDC}"
    )


def print_combinatorial_complexity():
    """Print the combinatorial complexity of testing different configurations"""
    print(
        f"\n{Colors.BOLD}{Colors.HEADER}===== COMBINATORIAL COMPLEXITY ANALYSIS ====={Colors.ENDC}"
    )

    # Analysis for different committee sizes
    committee_sizes = [5, 7, 11, 13, 23, 25, 47, 49]
    vote_options = 3  # Agree, Disagree, Timeout (removed Idle)

    print(f"\n{Colors.BOLD}Vote combinations per committee size:{Colors.ENDC}")
    for size in committee_sizes:
        # Full combinatorial (all permutations)
        permutations = vote_options**size

        # Reduced combinations (equivalence classes)
        # Formula for the number of ways to distribute n validators across 3 vote types: (n+2)!/(n!*2!)
        reduced = ((size + 3 - 1) * (size + 3 - 2)) // 2

        print(
            f"  Size {size}: {permutations:,} vote permutations, {reduced:,} vote distributions"
        )

    # Analysis for multiple rounds
    print(
        f"\n{Colors.BOLD}Scenario combinations for small committee sizes:{Colors.ENDC}"
    )
    for rounds in range(1, 4):
        size = 3  # Using smallest committee size
        reduced = ((size + 3 - 1) * (size + 3 - 2)) // 2
        total_scenarios = reduced**rounds

        print(
            f"  {rounds} rounds, committee size {size}: {total_scenarios:,} scenarios"
        )

    print(
        f"\n{Colors.YELLOW}Note: The combinatorial space grows extremely rapidly!{Colors.ENDC}"
    )
    print(
        f"{Colors.YELLOW}Recommendation: Use statistical sampling or limit committee sizes to 3-5.{Colors.ENDC}"
    )


if __name__ == "__main__":
    # Print complexity analysis first
    print_combinatorial_complexity()

    # Run a limited set of combinatorial tests
    # Using very small committee sizes to avoid combinatorial explosion
    run_combinatorial_tests(
        committee_sizes=[5, 7, 11],
        max_rounds=2,
        limit_combinations=True,
        max_scenarios=50,
    )

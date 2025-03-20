"""
Statistical Fee Distribution Testing

This module uses statistical sampling with prior probabilities to test
fee distribution across likely scenarios.
"""

import random
from typing import Dict, List, Tuple
from custom_types import (
    FeeDistribution, FeeEntry, TransactionBudget, 
    TransactionRoundResults, Round, Rotation, Appeal
)
from distribute_fees import distribute_fees
from constants import addresses_pool, round_sizes
from utils import pretty_print_fee_distribution, pretty_print_transaction_results, Colors

# Prior probabilities for different vote types
VOTE_PRIORS = {
    "Agree": 0.7,    # Most validators tend to agree in healthy networks
    "Disagree": 0.2, 
    "Timeout": 0.1
    # "Idle" is not included in the valid VoteType literal union in custom_types.py
}

# Prior probabilities for different round types
ROUND_TYPE_PRIORS = {
    "normal_round": 0.7,
    "appeal_round": 0.3
}

# Prior probability of consensus in a round
CONSENSUS_PRIORS = {
    "strong_consensus": 0.6,  # 80%+ agreement
    "weak_consensus": 0.3,    # 51-79% agreement
    "split": 0.1              # No clear majority
}

def initialize_fee_distribution() -> FeeDistribution:
    """Initialize a new fee distribution object"""
    fee_entries = {}
    for addr in addresses_pool:
        fee_entries[addr] = FeeEntry(
            leader=0, leader_node=0, validator_node=0,
            sender=0, sender_node=0, appealant=0, appealant_node=0
        )
    return FeeDistribution(fees=fee_entries)

def generate_statistical_vote_distribution(committee_size: int, 
                                          consensus_type: str) -> Dict[str, str]:
    """
    Generate votes based on statistical priors and desired consensus
    
    Args:
        committee_size: Number of validators
        consensus_type: Type of consensus to generate
        
    Returns:
        Dictionary mapping addresses to votes
    """
    votes = {}
    
    # Determine majority vote based on probabilities
    vote_options = list(VOTE_PRIORS.keys())
    majority_vote = random.choices(vote_options, 
                                  weights=[VOTE_PRIORS[v] for v in vote_options], 
                                  k=1)[0]
    
    # Determine agreement percentage based on consensus type
    if consensus_type == "strong_consensus":
        agreement_pct = random.uniform(0.8, 1.0)
    elif consensus_type == "weak_consensus":
        agreement_pct = random.uniform(0.51, 0.79)
    else:  # split
        agreement_pct = random.uniform(0.4, 0.5)
    
    # Number of validators with the majority opinion
    majority_count = int(committee_size * agreement_pct)
    
    # Assign the majority vote
    for i in range(majority_count):
        votes[addresses_pool[i]] = majority_vote
    
    # Assign random votes to the rest
    remaining_options = [v for v in vote_options if v != majority_vote]
    for i in range(majority_count, committee_size):
        votes[addresses_pool[i]] = random.choices(
            remaining_options, 
            weights=[VOTE_PRIORS[v] for v in remaining_options],
            k=1
        )[0]
    
    # Randomly select a leader and add leader receipt
    leader_idx = random.randint(0, committee_size-1)
    leader_addr = addresses_pool[leader_idx]
    votes[leader_addr] = ["LeaderReceipt", votes[leader_addr]] if isinstance(votes[leader_addr], str) else ["LeaderReceipt"] + votes[leader_addr]
    
    return votes

def generate_statistical_scenario(num_rounds: int = None) -> Tuple[TransactionRoundResults, TransactionBudget]:
    """
    Generate a statistically likely scenario
    
    Args:
        num_rounds: Number of rounds (if None, chosen based on ROUND_TYPE_PRIORS)
        
    Returns:
        Tuple of (transaction_results, transaction_budget)
    """
    # Determine if this is an appeal scenario
    if num_rounds is None:
        has_appeal = random.choices(
            [True, False], 
            weights=[ROUND_TYPE_PRIORS["appeal_round"], ROUND_TYPE_PRIORS["normal_round"]], 
            k=1
        )[0]
        num_rounds = random.randint(2, 3) if has_appeal else 1
    
    rounds = []
    
    # Generate each round
    for i in range(num_rounds):
        # Committee size - use round_sizes or random if out of bounds
        committee_size = round_sizes[i] if i < len(round_sizes) else random.choice([5, 7, 11, 13, 23])
        
        # For first round, distribution varies
        if i == 0:
            consensus_type = random.choices(
                list(CONSENSUS_PRIORS.keys()), 
                weights=list(CONSENSUS_PRIORS.values()), 
                k=1
            )[0]
        # For appeal rounds, tendency toward stronger consensus
        else:
            consensus_weights = [0.7, 0.2, 0.1]  # Higher chance of strong consensus
            consensus_type = random.choices(
                list(CONSENSUS_PRIORS.keys()), 
                weights=consensus_weights, 
                k=1
            )[0]
        
        # Generate votes
        votes = generate_statistical_vote_distribution(committee_size, consensus_type)
        
        # Create round and add to list
        rotation = Rotation(votes=votes)
        round_obj = Round(rotations=[rotation])
        rounds.append(round_obj)
    
    # Create transaction results
    transaction_results = TransactionRoundResults(rounds=rounds)
    
    # Create transaction budget
    appeals = []
    if num_rounds > 1:
        appealant_addr = random.choice(addresses_pool[500:600])  # Use different address range
        appeals = [Appeal(appealantAddress=appealant_addr, appealBond=300)]
    
    transaction_budget = TransactionBudget(
        leaderTimeout=100,
        validatorsTimeout=200,
        appealRounds=num_rounds,
        rotations=[1] * num_rounds,
        senderAddress=random.choice(addresses_pool[100:200]),
        appeals=appeals
    )
    
    return transaction_results, transaction_budget

def run_statistical_tests(num_tests: int = 20):
    """
    Run a series of statistical tests with different scenarios
    
    Args:
        num_tests: Number of test scenarios to generate
    """
    print(f"\n{Colors.BOLD}{Colors.HEADER}===== STATISTICAL FEE DISTRIBUTION TESTS ====={Colors.ENDC}")
    print(f"{Colors.YELLOW}(Running {num_tests} statistically generated scenarios){Colors.ENDC}")
    
    # Configure test distribution
    single_round_tests = int(num_tests * 0.6)  # 60% single-round
    appeal_tests = num_tests - single_round_tests  # 40% appeal scenarios
    
    # Run single round tests
    for i in range(single_round_tests):
        transaction_results, transaction_budget = generate_statistical_scenario(num_rounds=1)
        run_test(i, transaction_results, transaction_budget, "SINGLE-ROUND")
    
    # Run appeal scenario tests
    for i in range(appeal_tests):
        rand_rounds = random.randint(2, 3)
        transaction_results, transaction_budget = generate_statistical_scenario(num_rounds=rand_rounds)
        run_test(i + single_round_tests, transaction_results, transaction_budget, "APPEAL")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}===== ALL STATISTICAL TESTS COMPLETED ====={Colors.ENDC}")

def run_test(test_index: int, transaction_results: TransactionRoundResults, 
            transaction_budget: TransactionBudget, test_type: str):
    """Run a single test and display results"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}=== TEST {test_index+1}: {test_type} SCENARIO ==={Colors.ENDC}")
    
    # Initialize fee distribution
    fee_distribution = initialize_fee_distribution()
    
    print(f"{Colors.BOLD}{Colors.BLUE}Budget:{Colors.ENDC}")
    print(f"  Leader Timeout: {transaction_budget.leaderTimeout}")
    print(f"  Validators Timeout: {transaction_budget.validatorsTimeout}")
    print(f"  Appeal Rounds: {transaction_budget.appealRounds}")
    print(f"  Rotations: {transaction_budget.rotations}")
    if transaction_budget.appeals:
        for appeal in transaction_budget.appeals:
            print(f"  Appeal Bond: {appeal.appealBond}")
            print(f"  Appealant: {appeal.appealantAddress[:8]}...{appeal.appealantAddress[-6:]}")
    print()
    
    # Distribute fees
    result, round_labels = distribute_fees(
        fee_distribution=fee_distribution,
        transaction_results=transaction_results,
        transaction_budget=transaction_budget,
        verbose=False
    )
    
    # Show transaction structure with round labels
    pretty_print_transaction_results(transaction_results, round_labels)
    
    # Print fee distribution 
    pretty_print_fee_distribution(result.model_dump()["fees"])

if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)
    
    # Run tests
    run_statistical_tests(20)  # Generate 20 statistical scenarios

"""
Fee Distribution Test Scenarios

This file contains various test scenarios for the distribute_fees function.
Each scenario tests a different aspect of fee distribution logic.
"""

import json
from typing import Dict, List

from custom_types import (
    FeeDistribution, FeeEntry, TransactionBudget, 
    TransactionRoundResults, Round, Rotation, Appeal
)
from distribute_fees import distribute_fees
from constants import addresses_pool
from utils import pretty_print_fee_distribution, pretty_print_transaction_results, Colors

def initialize_fee_distribution() -> FeeDistribution:
    """
    Initialize a new fee distribution object.
    
    Returns:
        An empty fee distribution
    """
    fee_entries = {}
    for addr in addresses_pool:
        fee_entries[addr] = FeeEntry(
            leader=0,
            leader_node=0,
            validator_node=0,
            sender=0,
            sender_node=0,
            appealant=0,
            appealant_node=0
        )
    
    return FeeDistribution(fees=fee_entries)

def run_scenario_1():
    """
    Scenario 1: Basic normal round with validators in agreement.
    """
    print(f"\n{Colors.BOLD}{Colors.GREEN}=== SCENARIO 1: NORMAL ROUND WITH AGREEMENT ==={Colors.ENDC}")
    
    # Create a rotation with 5 validators in agreement
    rotation = Rotation(votes={
        addresses_pool[0]: ["LeaderReceipt", "Agree"],
        addresses_pool[1]: "Agree",
        addresses_pool[2]: "Agree",
        addresses_pool[3]: "Agree",
        addresses_pool[4]: "Agree"
    })
    
    # Create a round with the rotation
    round = Round(rotations=[rotation])
    
    # Create transaction results
    transaction_results = TransactionRoundResults(rounds=[round])
    
    # Create transaction budget
    transaction_budget = TransactionBudget(
        leaderTimeout=100,
        validatorsTimeout=200,
        appealRounds=1,
        rotations=[2],
        senderAddress=addresses_pool[10],
        appeals=[]
    )
    
    print(f"{Colors.BOLD}{Colors.BLUE}Budget:{Colors.ENDC}")
    print(f"  Leader Timeout: {transaction_budget.leaderTimeout}")
    print(f"  Validators Timeout: {transaction_budget.validatorsTimeout}")
    print(f"  Appeal Rounds: {transaction_budget.appealRounds}")
    print(f"  Rotations: {transaction_budget.rotations}\n")
    
    # Initialize fee distribution
    fee_distribution = initialize_fee_distribution()
    
    print(f"{Colors.BOLD}{Colors.YELLOW}Computing fee distribution...{Colors.ENDC}\n")
    
    # Distribute fees
    result, round_labels = distribute_fees(
        fee_distribution=fee_distribution,
        transaction_results=transaction_results,
        transaction_budget=transaction_budget,
        verbose=False  # Set to False as we'll display everything together
    )
    
    # Show transaction structure with round labels
    pretty_print_transaction_results(transaction_results, round_labels)
    
    # Print fee distribution 
    pretty_print_fee_distribution(result.dict()["fees"])

def run_scenario_2():
    """
    Scenario 2: Normal round with split votes.
    """
    print(f"\n{Colors.BOLD}{Colors.YELLOW}=== SCENARIO 2: NORMAL ROUND WITH SPLIT VOTES ==={Colors.ENDC}")
    
    # Create a rotation with split votes
    rotation = Rotation(votes={
        addresses_pool[0]: ["LeaderReceipt", "Agree"],
        addresses_pool[1]: "Agree",
        addresses_pool[2]: "Disagree",
        addresses_pool[3]: "Disagree",
        addresses_pool[4]: "Timeout"
    })
    
    # Create a round with the rotation
    round = Round(rotations=[rotation])
    
    # Create transaction results
    transaction_results = TransactionRoundResults(rounds=[round])
        
    # Create transaction budget
    transaction_budget = TransactionBudget(
        leaderTimeout=100,
        validatorsTimeout=200,
        appealRounds=1,
        rotations=[1],
        senderAddress=addresses_pool[10],
        appeals=[]
    )
    
    print(f"{Colors.BOLD}{Colors.BLUE}Budget:{Colors.ENDC}")
    print(f"  Leader Timeout: {transaction_budget.leaderTimeout}")
    print(f"  Validators Timeout: {transaction_budget.validatorsTimeout}")
    print(f"  Appeal Rounds: {transaction_budget.appealRounds}")
    print(f"  Rotations: {transaction_budget.rotations}\n")
    
    # Initialize fee distribution
    fee_distribution = initialize_fee_distribution()
    
    print(f"{Colors.BOLD}{Colors.YELLOW}Computing fee distribution...{Colors.ENDC}\n")
    
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
    pretty_print_fee_distribution(result.dict()["fees"])

def run_scenario_3():
    """
    Scenario 3: Appeal scenario with sender and appealant.
    """
    print(f"\n{Colors.BOLD}{Colors.RED}=== SCENARIO 3: APPEAL SCENARIO ==={Colors.ENDC}")
    
    # First round - normal round with disagreement
    rotation1 = Rotation(votes={
        addresses_pool[0]: ["LeaderReceipt", "Agree"],
        addresses_pool[1]: "Disagree",
        addresses_pool[2]: "Disagree",
        addresses_pool[3]: "Disagree",
        addresses_pool[4]: "Timeout"
    })
    
    round1 = Round(rotations=[rotation1])
    
    # Second round - appeal round with agreement
    rotation2 = Rotation(votes={
        addresses_pool[5]: "Agree",
        addresses_pool[6]: "Agree",
        addresses_pool[7]: "Agree",
        addresses_pool[8]: "Agree",
        addresses_pool[9]: "Agree",
        addresses_pool[10]: "Agree",
        addresses_pool[11]: "Agree"
    })
    
    round2 = Round(rotations=[rotation2])
    
    # Third round - normal round with agreement
    rotation3 = Rotation(votes={
        addresses_pool[1]: ["LeaderReceipt", "Agree"],
        addresses_pool[2]: "Agree",
        addresses_pool[3]: "Agree",
        addresses_pool[4]: "Agree",
        addresses_pool[5]: "Agree",
        addresses_pool[6]: "Agree",
        addresses_pool[7]: "Agree",
        addresses_pool[8]: "Agree",
        addresses_pool[9]: "Agree",
        addresses_pool[10]: "Agree",
        addresses_pool[11]: "Agree"
    })
    
    round3 = Round(rotations=[rotation3])
    
    # Create transaction results with two rounds
    transaction_results = TransactionRoundResults(rounds=[round1, round2, round3])
    
    # Create appeal
    appeal = Appeal(appealantAddress=addresses_pool[15], appealBond=300)
    
    # Create transaction budget with appeal
    transaction_budget = TransactionBudget(
        leaderTimeout=100,
        validatorsTimeout=200,
        appealRounds=2,
        rotations=[1, 2],
        senderAddress=addresses_pool[10],
        appeals=[appeal]
    )
    
    print(f"{Colors.BOLD}{Colors.BLUE}Budget:{Colors.ENDC}")
    print(f"  Leader Timeout: {transaction_budget.leaderTimeout}")
    print(f"  Validators Timeout: {transaction_budget.validatorsTimeout}")
    print(f"  Appeal Rounds: {transaction_budget.appealRounds}")
    print(f"  Rotations: {transaction_budget.rotations}")
    print(f"  Appeal Bond: {appeal.appealBond}")
    print(f"  Appealant: {appeal.appealantAddress[:8]}...{appeal.appealantAddress[-6:]}\n")
    
    # Initialize fee distribution
    fee_distribution = initialize_fee_distribution()
    
    print(f"{Colors.BOLD}{Colors.YELLOW}Computing fee distribution...{Colors.ENDC}\n")
    
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
    pretty_print_fee_distribution(result.dict()["fees"])

def run_scenario_4():
    """
    Scenario 4: Complex scenario with multiple rounds and rotations.
    """
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== SCENARIO 4: COMPLEX MULTI-ROUND SCENARIO ==={Colors.ENDC}")
    
    # First round with multiple rotations
    rotation1_1 = Rotation(votes={
        addresses_pool[0]: ["LeaderReceipt", "Agree"],
        addresses_pool[1]: "Agree",
        addresses_pool[2]: "Timeout",
        addresses_pool[3]: "Agree",
        addresses_pool[4]: "Timeout"
    })
    
    rotation1_2 = Rotation(votes={
        addresses_pool[5]: ["LeaderReceipt", "Agree"],
        addresses_pool[1]: "Disagree",
        addresses_pool[2]: "Timeout",
        addresses_pool[3]: "Agree",
        addresses_pool[4]: "Timeout"
    })
    
    round1 = Round(rotations=[rotation1_1, rotation1_2])
    
    # Second round
    rotation2 = Rotation(votes={
        addresses_pool[6]: "Agree",
        addresses_pool[7]: "Disagree",
        addresses_pool[8]: "Agree",
        addresses_pool[9]: "Timeout",
        addresses_pool[10]: "Timeout",
        addresses_pool[11]: "Agree",
        addresses_pool[12]: "Disagree"
    })
    
    round2 = Round(rotations=[rotation2])
    
    # Third round (empty appeal round)
    round3 = Round(rotations=[])
    
    # Create transaction results
    transaction_results = TransactionRoundResults(rounds=[round1, round2, round3])
        
    # Create appeal
    appeal1 = Appeal(appealantAddress=addresses_pool[15], appealBond=300)
    
    # Create transaction budget
    transaction_budget = TransactionBudget(
        leaderTimeout=100,
        validatorsTimeout=200,
        appealRounds=3,
        rotations=[1, 2, 3],
        senderAddress=addresses_pool[10],
        appeals=[appeal1]
    )
    
    print(f"{Colors.BOLD}{Colors.BLUE}Budget:{Colors.ENDC}")
    print(f"  Leader Timeout: {transaction_budget.leaderTimeout}")
    print(f"  Validators Timeout: {transaction_budget.validatorsTimeout}")
    print(f"  Appeal Rounds: {transaction_budget.appealRounds}")
    print(f"  Rotations: {transaction_budget.rotations}")
    print(f"  Appeal Bond: {appeal1.appealBond}")
    print(f"  Appealant: {appeal1.appealantAddress[:8]}...{appeal1.appealantAddress[-6:]}\n")
    
    # Initialize fee distribution
    fee_distribution = initialize_fee_distribution()
    
    print(f"{Colors.BOLD}{Colors.YELLOW}Computing fee distribution...{Colors.ENDC}\n")
    
    # Distribute fees
    result, round_labels = distribute_fees(
        fee_distribution=fee_distribution,
        transaction_results=transaction_results,
        transaction_budget=transaction_budget,
        verbose=True
    )

    # Show transaction structure with round labels
    pretty_print_transaction_results(transaction_results, round_labels)
    
    # Print fee distribution 
    pretty_print_fee_distribution(result.dict()["fees"])

def run_scenario_5():
    """
    Scenario 1: Basic normal round with validators in agreement.
    """
    print(f"\n{Colors.BOLD}{Colors.GREEN}=== SCENARIO 1: NORMAL ROUND WITH AGREEMENT ==={Colors.ENDC}")
    
    # Create a rotation with 5 validators in agreement
    rotation = Rotation(votes={
        addresses_pool[0]: ["LeaderReceipt", "Agree"],
        addresses_pool[1]: "Agree",
        addresses_pool[2]: "Agree",
        addresses_pool[3]: "Agree",
        addresses_pool[4]: "Disagree"
    })
    
    # Create a round with the rotation
    round = Round(rotations=[rotation])
    
    # Create transaction results
    transaction_results = TransactionRoundResults(rounds=[round])
    
    # Create transaction budget
    transaction_budget = TransactionBudget(
        leaderTimeout=100,
        validatorsTimeout=200,
        appealRounds=1,
        rotations=[2],
        senderAddress=addresses_pool[10],
        appeals=[]
    )
    
    print(f"{Colors.BOLD}{Colors.BLUE}Budget:{Colors.ENDC}")
    print(f"  Leader Timeout: {transaction_budget.leaderTimeout}")
    print(f"  Validators Timeout: {transaction_budget.validatorsTimeout}")
    print(f"  Appeal Rounds: {transaction_budget.appealRounds}")
    print(f"  Rotations: {transaction_budget.rotations}\n")
    
    # Initialize fee distribution
    fee_distribution = initialize_fee_distribution()
    
    print(f"{Colors.BOLD}{Colors.YELLOW}Computing fee distribution...{Colors.ENDC}\n")
    
    # Distribute fees
    result, round_labels = distribute_fees(
        fee_distribution=fee_distribution,
        transaction_results=transaction_results,
        transaction_budget=transaction_budget,
        verbose=False  # Set to False as we'll display everything together
    )
    
    # Show transaction structure with round labels
    pretty_print_transaction_results(transaction_results, round_labels)
    
    # Print fee distribution 
    pretty_print_fee_distribution(result.dict()["fees"])

if __name__ == "__main__":
    print(f"\n{Colors.BOLD}{Colors.HEADER}===== FEE DISTRIBUTION TEST SCENARIOS ====={Colors.ENDC}")
    print(f"{Colors.YELLOW}(Note: Each scenario tests different aspects of fee distribution logic){Colors.ENDC}")
    
    # Run all scenarios
    run_scenario_1()
    run_scenario_2()
    run_scenario_3()
    run_scenario_4()
    run_scenario_5()
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}===== ALL SCENARIOS COMPLETED ====={Colors.ENDC}")
    # Alternatively, run specific scenarios for targeted testing
    # run_scenario_1() 
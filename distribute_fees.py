from typing import List
from math import floor
from majority import compute_majority, who_is_in_majority, normalize_vote
from utils import pretty_print_fee_distribution
from custom_types import (
    Round, TransactionBudget, FeeDistribution,
    TransactionRoundResults, RoundLabel
)
from constants import penalty_reward_coefficient

def label_rounds(transaction_results: TransactionRoundResults) -> List[RoundLabel]:
    """
    Label each round based on its index.
    Returns a list of labels.
    
    Args:
        transaction_results: Validated transaction rounds
        
    Returns:
        List of round labels
    """
    # Extract rounds for processing
    rounds = []
    for i, round_obj in enumerate(transaction_results.rounds):
        # Get the last rotation's votes from each round or empty dict if no rotations
        if round_obj.rotations:
            rounds.append(round_obj.rotations[-1].votes)
        else:
            rounds.append({})
    
    labels = ["normal_round"]
    
    if len(rounds) == 1:
        return labels

    for i, round in enumerate(rounds):
        if i == 0:
            continue
        if len(round) == 0:
            labels.append("empty_round")
        if i%2 == 1:
            if len(rounds[i-1]) == 1 and i+1 < len(rounds) and len(rounds[i+1]) == 1:
                labels.append("appeal_leader_timeout_unsuccessful")
            if len(rounds[i-1]) == 1 and i+1 < len(rounds) and len(rounds[i+1]) > 1:
                labels.append("appeal_leader_timeout_successful")
            if compute_majority(rounds[i-1]) == "UNDETERMINED" and i+1 < len(rounds) and compute_majority(rounds[i+1]) != "UNDETERMINED":
                labels.append("appeal_leader_successful")
            if compute_majority(rounds[i-1]) == "UNDETERMINED" and i+1 < len(rounds) and compute_majority(rounds[i+1]) == "UNDETERMINED":
                labels.append("appeal_leader_unsuccessful")

            empty_candidate = i-1
            while empty_candidate >= 0 and rounds[empty_candidate] == "empty_round" and compute_majority(rounds[empty_candidate]) != "UNDETERMINED":
                empty_candidate -= 2
            if compute_majority(rounds[empty_candidate]) != "UNDETERMINED":
                if empty_candidate >= 0 and compute_majority(round) != compute_majority(rounds[empty_candidate]): 
                    labels.append("appeal_validator_successful")
                else:
                    labels.append("appeal_validator_unsuccessful")
        else:
            if len(round) == 1:
                labels.append("leader_timeout")
            else:
                labels.append("normal_round")
    
    # Handle special cases with the reversed list
    reverse_labels = labels[::-1]
    reverse_rounds = rounds[::-1]
    
    for i in range(len(reverse_rounds)):
        if i + 2 < len(reverse_rounds):
            if reverse_labels[i] == "normal_round" and \
            i + 1 < len(reverse_labels) and "appeal" in reverse_labels[i+1] and \
            i + 2 < len(reverse_rounds) and compute_majority(reverse_rounds[i+2]) == "UNDETERMINED":
                if "unsuccessful" in reverse_labels[i+1]:
                    reverse_labels[i] = "split_previous_appeal_bond"
                else:
                    reverse_labels[i+2] = "validators_penalty_only_round"
            
            if i < len(labels) and labels[i] == "leader_timeout" and \
            i + 1 < len(labels) and labels[i+1] == "appeal_leader_timeout_unsuccessful" and \
            i + 2 < len(labels) and labels[i+2] == "leader_timeout":
                reverse_labels[i] = "leader_timeout_50_previous_appeal_bond"
                reverse_labels[i+2] = "leader_timeout_50_percent"

            if reverse_labels[i] == "normal_round" and \
            i + 1 < len(reverse_labels) and "appeal_leader_timeout_successful" == reverse_labels[i+1] and \
            i + 2 < len(reverse_labels) and reverse_labels[i+2] == "leader_timeout":
                reverse_labels[i] = "leader_timeout_150_previous_normal_round"
                reverse_labels[i+2] = "skip_round"

    return reverse_labels[::-1]

def distribute_round(
    round: Round,
    round_index: int,
    label: RoundLabel,
    transaction_budget: TransactionBudget,
    fee_distribution: FeeDistribution
) -> FeeDistribution:
    """
    Distribute fees for a single round based on its label.
    
    Args:
        round: Round data with rotations
        round_index: Index of the round
        label: Round label
        transaction_budget: Transaction budget parameters
        fee_distribution: Current fee distribution
        
    Returns:
        Updated fee distribution
    """
    # Skip processing for certain round types
    if label == "empty_round" or label == "skip_round":
        return fee_distribution
        
    # If round has no rotations, return unchanged
    if not round.rotations:
        return fee_distribution
        
    # Get the votes from the last rotation
    votes = round.rotations[-1].votes
    
    if label == "normal_round":
        majority = compute_majority(votes)
        if majority == "UNDETERMINED":  # equal split
            # Get first address as leader
            first_addr = next(iter(votes.keys()), None)
            if first_addr:
                if first_addr in fee_distribution.fees:
                    fee_distribution.fees[first_addr].leader_node += transaction_budget.leaderTimeout
                
                # Distribute to all validators
                for addr in votes.keys():
                    if addr in fee_distribution.fees:
                        fee_distribution.fees[addr].validator_node += transaction_budget.validatorsTimeout
        else:
            # Get addresses in majority
            majority_addresses, minority_addresses = who_is_in_majority(votes, majority)
            # Distribute to majority validators
            for addr in majority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[addr].validator_node += transaction_budget.validatorsTimeout
            
            # Distribute to minority validators
            for addr in minority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[addr].validator_node -= penalty_reward_coefficient * transaction_budget.validatorsTimeout

            # Give leader fee to first address
            first_addr = next(iter(votes.keys()), None)
            if first_addr and first_addr in fee_distribution.fees:
                fee_distribution.fees[first_addr].leader_node += transaction_budget.leaderTimeout
    
    elif label == "validators_penalty_only_round":
        penalizable_votes = ["Disagree", "Timeout"]
        penalizable_addresses = [addr for addr in votes.keys() if normalize_vote(votes[addr]) in penalizable_votes]

        for addr in penalizable_addresses:
            if addr in fee_distribution.fees:
                fee_distribution.fees[addr].validator_node -= penalty_reward_coefficient * transaction_budget.validatorsTimeout

    elif label == "appeal_leader_timeout_unsuccessful":
        sender_address = transaction_budget.senderAddress
        
        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index <= len(transaction_budget.appeals):
            appeal = transaction_budget.appeals[floor(round_index/2)]
            appealant_address = appeal.appealantAddress
            
            # Update fees
            if sender_address in fee_distribution.fees:
                fee_distribution.fees[sender_address].sender_node += appeal.appealBond
            
            if appealant_address in fee_distribution.fees:
                fee_distribution.fees[appealant_address].appealant_node -= appeal.appealBond
    
    elif label == "appeal_leader_timeout_successful":
        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index <= len(transaction_budget.appeals):
            appeal = transaction_budget.appeals[floor(round_index/2)]
            appealant_address = appeal.appealantAddress
            
            if appealant_address in fee_distribution.fees:
                fee_distribution.fees[appealant_address].appealant_node += appeal.appealBond
                fee_distribution.fees[appealant_address].appealant_node += transaction_budget.leaderTimeout / 2
    
    elif label == "appeal_leader_successful":
        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index <= len(transaction_budget.appeals):
            appeal = transaction_budget.appeals[floor(round_index/2)]
            appealant_address = appeal.appealantAddress
            
            if appealant_address in fee_distribution.fees:
                fee_distribution.fees[appealant_address].appealant_node += appeal.appealBond
                fee_distribution.fees[appealant_address].appealant_node += transaction_budget.leaderTimeout
    
    elif label == "appeal_leader_unsuccessful":
        sender_address = transaction_budget.senderAddress
        
        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index <= len(transaction_budget.appeals):
            appeal = transaction_budget.appeals[floor(round_index/2)]
            appealant_address = appeal.appealantAddress
            
            if sender_address in fee_distribution.fees:
                fee_distribution.fees[sender_address].sender_node += appeal.appealBond
            
            if appealant_address in fee_distribution.fees:
                fee_distribution.fees[appealant_address].appealant_node -= appeal.appealBond
    
    elif label == "appeal_validator_successful":
        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index <= len(transaction_budget.appeals):
            appeal = transaction_budget.appeals[floor(round_index/2)]
            appealant_address = appeal.appealantAddress
            
            if appealant_address in fee_distribution.fees:
                fee_distribution.fees[appealant_address].appealant_node += appeal.appealBond
                fee_distribution.fees[appealant_address].appealant_node += transaction_budget.leaderTimeout
            
            majority = compute_majority(votes)
            majority_addresses, minority_addresses = who_is_in_majority(votes, majority)
            
            # Distribute to all validators
            for addr in majority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[addr].validator_node += transaction_budget.validatorsTimeout
            
            # Add penalty for minority validators
            for addr in minority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[addr].validator_node -= penalty_reward_coefficient * transaction_budget.validatorsTimeout
    
    elif label == "appeal_validator_unsuccessful":
        sender_address = transaction_budget.senderAddress
        
        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index <= len(transaction_budget.appeals):
            appeal = transaction_budget.appeals[floor(round_index/2)]
            appealant_address = appeal.appealantAddress
            
            majority = compute_majority(votes)
            majority_addresses, minority_addresses = who_is_in_majority(votes, majority)
            
            # Distribute to all validators
            for addr in majority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[addr].validator_node += transaction_budget.validatorsTimeout
            
            # Add penalty for minority validators
            for addr in minority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[addr].validator_node -= penalty_reward_coefficient * transaction_budget.validatorsTimeout
            
            if sender_address in fee_distribution.fees:
                fee_distribution.fees[sender_address].sender_node += appeal.appealBond
            
            if appealant_address in fee_distribution.fees:
                fee_distribution.fees[appealant_address].appealant_node -= appeal.appealBond
    
    elif label == "leader_timeout_50_percent":
        first_addr = next(iter(votes.keys()), None)
        if first_addr and first_addr in fee_distribution.fees:
            fee_distribution.fees[first_addr].leader_node += transaction_budget.leaderTimeout / 2
    
    elif label == "split_previous_appeal_bond":
        majority = compute_majority(votes)
        majority_addresses, minority_addresses = who_is_in_majority(votes, majority)
        
        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index > 0 and round_index - 1 <= len(transaction_budget.appeals):
            appeal_bond = transaction_budget.appeals[floor(round_index/2) - 1].appealBond
            
            # Distribute to majority validators
            for addr in majority_addresses:
                if addr in fee_distribution.fees and majority_addresses:
                    fee_distribution.fees[addr].validator_node += transaction_budget.validatorsTimeout
                    fee_distribution.fees[addr].validator_node += appeal_bond / len(majority_addresses)
            
            # Add penalty for minority validators 
            for addr in minority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[addr].validator_node -= penalty_reward_coefficient * transaction_budget.validatorsTimeout
    
    elif label == "leader_timeout_50_previous_appeal_bond":
        sender_address = transaction_budget.senderAddress
        first_addr = next(iter(votes.keys()), None)
        
        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index > 0 and round_index - 1 <= len(transaction_budget.appeals):
            appeal_bond = transaction_budget.appeals[floor(round_index/2) - 1].appealBond
            
            if first_addr and first_addr in fee_distribution.fees:
                fee_distribution.fees[first_addr].leader_node += appeal_bond / 2
            
            if sender_address in fee_distribution.fees:
                fee_distribution.fees[sender_address].sender_node += appeal_bond / 2
    
    elif label == "leader_timeout_150_previous_normal_round":
        majority = compute_majority(votes)
        majority_addresses, minority_addresses = who_is_in_majority(votes, majority)
        sender_address = transaction_budget.senderAddress
        first_addr = next(iter(votes.keys()), None)

        if first_addr and first_addr in fee_distribution.fees:
            fee_distribution.fees[first_addr].leader_node += transaction_budget.leaderTimeout * 1.5
        if sender_address in fee_distribution.fees:
            fee_distribution.fees[sender_address].sender_node += transaction_budget.leaderTimeout / 2
        
        # Distribute to majority validators
        for addr in majority_addresses:
            if addr in fee_distribution.fees and majority_addresses:
                fee_distribution.fees[addr].validator_node += transaction_budget.validatorsTimeout
                fee_distribution.fees[addr].validator_node += appeal_bond / len(majority_addresses)
                
        # Add penalty for minority validators
        for addr in minority_addresses:
            if addr in fee_distribution.fees:
                fee_distribution.fees[addr].validator_node -= penalty_reward_coefficient * transaction_budget.validatorsTimeout

    else:
        raise ValueError(f"Invalid label: {label}")

    return fee_distribution

def distribute_fees(
    fee_distribution: FeeDistribution, 
    transaction_results: TransactionRoundResults, 
    transaction_budget: TransactionBudget, 
    verbose: bool = False
) -> tuple[FeeDistribution, List[RoundLabel]]:
    """
    Compute total fee distribution across all rounds.
    
    Args:
        fee_distribution: Initial fee distribution
        transaction_results: Transaction rounds
        transaction_budget: Budget parameters
        verbose: Whether to print detailed output
        
    Returns:
        Tuple of (updated fee distribution, round labels)
    """
    # Get labels for all rounds
    labels = label_rounds(transaction_results)
    
    # Process each round with its label
    for i, round_obj in enumerate(transaction_results.rounds):
        if i < len(labels):
            fee_distribution = distribute_round(
                round=round_obj,
                round_index=i,
                label=labels[i],
                transaction_budget=transaction_budget,
                fee_distribution=fee_distribution
            )

    if verbose:
        # Convert to dict for pretty printing
        pretty_print_fee_distribution(fee_distribution.dict()["fees"])

    return fee_distribution, labels

# TODO: add auto computing of bonds per unsuccesful appeal type


# TODO: show pretty prints on terminal
# TODO: build a frontend with streamlit so others can use it
# TODO: add unit tests
# TODO: add docs
from typing import List
from fee_simulator.models import Round, TransactionBudget, FeeEvent, EventSequence
from fee_simulator.core.majority import compute_majority, who_is_in_vote_majority, normalize_vote
from fee_simulator.core.bond_computing import compute_appeal_bond
from fee_simulator.constants import PENALTY_REWARD_COEFFICIENT

def apply_split_previous_appeal_bond(round: Round, round_index: int, budget: TransactionBudget, event_sequence: EventSequence) -> List[FeeEvent]:
    events = []
    if not round.rotations or not budget.appeals or round_index < 1 or round_index - 1 > len(budget.appeals):
        return events

    votes = round.rotations[-1].votes
    majority = compute_majority(votes)
    majority_addresses, minority_addresses = who_is_in_vote_majority(votes, majority)
    
    # Compute appeal bond for the previous appeal round (normal_round_index = round_index - 2)
    appeal_bond = compute_appeal_bond(
        normal_round_index=round_index - 2,
        leader_timeout=budget.leaderTimeout,
        validators_timeout=budget.validatorsTimeout,
    )

    # Distribute to validators
    if majority == "UNDETERMINED":
        for addr in votes.keys():
            events.append(FeeEvent(
                sequence_id=event_sequence.next_id(),
                address=addr,
                round_index=round_index,
                round_label="SPLIT_PREVIOUS_APPEAL_BOND",
                role="VALIDATOR",
                vote=normalize_vote(votes[addr]),
                hash="0xdefault",
                cost=0,
                staked=0,
                earned=appeal_bond / len(votes) + budget.validatorsTimeout,
                slashed=0,
                burned=0
            ))
    else:
        for addr in majority_addresses:
            events.append(FeeEvent(
                sequence_id=event_sequence.next_id(),
                address=addr,
                round_index=round_index,
                round_label="SPLIT_PREVIOUS_APPEAL_BOND",
                role="VALIDATOR",
                vote=normalize_vote(votes[addr]),
                hash="0xdefault",
                cost=0,
                staked=0,
                earned=budget.validatorsTimeout + (appeal_bond / len(majority_addresses) if majority_addresses else 0),
                slashed=0,
                burned=0
            ))
        for addr in minority_addresses:
            events.append(FeeEvent(
                sequence_id=event_sequence.next_id(),
                address=addr,
                round_index=round_index,
                round_label="SPLIT_PREVIOUS_APPEAL_BOND",
                role="VALIDATOR",
                vote=normalize_vote(votes[addr]),
                hash="0xdefault",
                cost=0,
                staked=0,
                earned=0,
                slashed=0,
                burned=PENALTY_REWARD_COEFFICIENT * budget.validatorsTimeout
            ))

    # Award the leader
    first_addr = next(iter(votes.keys()), None)
    if first_addr:
        events.append(FeeEvent(
            sequence_id=event_sequence.next_id(),
            address=first_addr,
            round_index=round_index,
            round_label="SPLIT_PREVIOUS_APPEAL_BOND",
            role="LEADER",
            vote=normalize_vote(votes[first_addr]),
            hash="0xdefault",
            cost=0,
            staked=0,
            earned=budget.leaderTimeout,
            slashed=0,
            burned=0
        ))

    return events
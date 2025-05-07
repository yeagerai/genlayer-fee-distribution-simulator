from typing import List
from math import floor
from fee_simulator.models import Round, TransactionBudget, FeeEvent, EventSequence
from fee_simulator.core.majority import normalize_vote

def apply_leader_timeout_50_previous_appeal_bond(round: Round, round_index: int, budget: TransactionBudget, event_sequence: EventSequence) -> List[FeeEvent]:
    events = []
    if not round.rotations or not budget.appeals or round_index < 1 or round_index - 1 > len(budget.appeals):
        return events

    votes = round.rotations[-1].votes
    sender_address = budget.senderAddress
    appeal = budget.appeals[floor(round_index / 2) - 1]
    appeal_bond = appeal.appealBond

    # Award half the appeal bond to the leader
    first_addr = next(iter(votes.keys()), None)
    if first_addr:
        events.append(FeeEvent(
            sequence_id=event_sequence.next_id(),
            address=first_addr,
            round_index=round_index,
            round_label="LEADER_TIMEOUT_50_PREVIOUS_APPEAL_BOND",
            role="LEADER",
            vote=normalize_vote(votes[first_addr]),
            hash="0xdefault",
            cost=0,
            staked=0,
            earned=appeal_bond / 2,
            slashed=0,
            burned=0
        ))

    # Award half the appeal bond to the sender
    events.append(FeeEvent(
        sequence_id=event_sequence.next_id(),
        address=sender_address,
        round_index=round_index,
        round_label="LEADER_TIMEOUT_50_PREVIOUS_APPEAL_BOND",
        role="SENDER",
        vote="NA",
        hash="0xdefault",
        cost=0,
        staked=0,
        earned=appeal_bond / 2,
        slashed=0,
        burned=0
    ))

    return events
from typing import List
from fee_simulator.models import (
    TransactionRoundResults,
    TransactionBudget,
    FeeEvent,
    EventSequence,
)
from fee_simulator.core.majority import (
    compute_majority,
    who_is_in_vote_majority,
    normalize_vote,
)
from fee_simulator.core.bond_computing import compute_appeal_bond
from fee_simulator.constants import PENALTY_REWARD_COEFFICIENT


def apply_split_previous_appeal_bond(
    transaction_results: TransactionRoundResults,
    round_index: int,
    budget: TransactionBudget,
    event_sequence: EventSequence,
) -> List[FeeEvent]:
    events = []
    round = transaction_results.rounds[round_index]
    if (
        not round.rotations
        or not budget.appeals
        or round_index < 1
        or round_index - 1 > len(budget.appeals)
    ):
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
    amount_to_split = appeal_bond - budget.leaderTimeout
    # Distribute to validators
    if majority == "UNDETERMINED":
        undet_split_amount = (amount_to_split * 10**18 // len(votes)) // 10**18
        for addr in votes.keys():
            events.append(
                FeeEvent(
                    sequence_id=event_sequence.next_id(),
                    address=addr,
                    round_index=round_index,
                    round_label="SPLIT_PREVIOUS_APPEAL_BOND",
                    role="VALIDATOR",
                    vote=normalize_vote(votes[addr]),
                    hash="0xdefault",
                    cost=0,
                    staked=0,
                    earned=undet_split_amount,  # + budget.validatorsTimeout,
                    slashed=0,
                    burned=0,
                )
            )
    else:
        agree_split_amount = (appeal_bond * 10**18 // len(majority_addresses)) // 10**18
        for addr in majority_addresses:
            events.append(
                FeeEvent(
                    sequence_id=event_sequence.next_id(),
                    address=addr,
                    round_index=round_index,
                    round_label="SPLIT_PREVIOUS_APPEAL_BOND",
                    role="VALIDATOR",
                    vote=normalize_vote(votes[addr]),
                    hash="0xdefault",
                    cost=0,
                    staked=0,
                    earned=agree_split_amount,  # + budget.validatorsTimeout,
                    slashed=0,
                    burned=0,
                )
            )
        for addr in minority_addresses:
            events.append(
                FeeEvent(
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
                    burned=PENALTY_REWARD_COEFFICIENT * budget.validatorsTimeout,
                )
            )

    # Award the leader
    first_addr = next(iter(votes.keys()), None)
    if first_addr:
        events.append(
            FeeEvent(
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
                burned=0,
            )
        )

    return events

from typing import List
from math import floor
from fee_simulator.models import (
    TransactionRoundResults,
    TransactionBudget,
    FeeEvent,
    EventSequence,
)
from fee_simulator.core.bond_computing import compute_appeal_bond


def apply_appeal_leader_timeout_successful(
    transaction_results: TransactionRoundResults,
    round_index: int,
    budget: TransactionBudget,
    event_sequence: EventSequence,
) -> List[FeeEvent]:
    events = []
    if not budget.appeals or round_index > len(budget.appeals):
        return events
    appeal = budget.appeals[floor(round_index / 2)]
    appealant_address = appeal.appealantAddress
    appeal_bond = compute_appeal_bond(
        normal_round_index=round_index - 1,
        leader_timeout=budget.leaderTimeout,
        validators_timeout=budget.validatorsTimeout,
    )
    events.append(
        FeeEvent(
            sequence_id=event_sequence.next_id(),
            address=appealant_address,
            round_index=round_index,
            round_label="APPEAL_LEADER_TIMEOUT_SUCCESSFUL",
            role="APPEALANT",
            earned=appeal_bond + budget.leaderTimeout / 2,
        )
    )
    return events

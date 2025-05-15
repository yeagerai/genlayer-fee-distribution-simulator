from typing import List
from fee_simulator.models import (
    FeeEvent,
    TransactionBudget
)
from fee_simulator.display.fee_distribution import display_fee_distribution
def compute_sender_refund(sender_address: str, fee_events: List[FeeEvent], transaction_budget: TransactionBudget) -> float:
    # TODO: when introducing toppers, we need to change this function
    sender_cost = 0
    total_paid_from_sender = 0
    for event in fee_events:
        # Skip unsuccessful appeal costs, if leader appeal we skip 2 rounds
        round_label = event.round_label if event.round_label is not None else ""
        if event.role == "APPEALANT":
            if event.earned > 0:
                total_paid_from_sender+=transaction_budget.leaderTimeout
            continue
        if "UNSUCCESSFUL" in round_label: 
            continue
        if round_label == "SPLIT_PREVIOUS_APPEAL_BOND":
            if event.role == "VALIDATOR":
                total_paid_from_sender+=transaction_budget.validatorsTimeout
                continue
            if event.role == "LEADER":
                total_paid_from_sender+=transaction_budget.leaderTimeout
                continue
        total_paid_from_sender += event.earned
        if event.address == sender_address:
            sender_cost += event.cost

    refund = sender_cost - total_paid_from_sender
    if refund < 0:
        display_fee_distribution(fee_events)
        raise ValueError(f"Total paid from sender is greater than sender cost: {total_paid_from_sender} > {sender_cost}")

    return refund


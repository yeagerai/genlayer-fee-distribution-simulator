from typing import List
from fee_simulator.models import (
    FeeEvent,
)

def compute_sender_refund(sender_address: str, fee_events: List[FeeEvent]) -> float:
    # TODO: when introducing toppers, we need to change this function
    cost = 0
    total_paid = 0
    for event in fee_events:
        # Skip unsuccessful appeal costs, if leader appeal we skip 2 rounds
        round_label = event.round_label if event.round_label is not None else ""
        round_index = event.round_index
        if event.role == "APPEALANT":
            continue
        if "UNSUCCESSFUL" in round_label: 
            if "VALIDATOR" in round_label:
                continue
            continue
        if event.round_index:
            if event.round_index == round_index + 1:
                continue
        total_paid += event.earned
        if event.address == sender_address:
            cost += event.cost
    refund = max(0, cost - total_paid)
    return refund


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

def compute_unsuccessful_leader_appeal_burn(current_round_index: int, appealant_address: str, fee_events: List[FeeEvent]) -> float:
    burn = 0
    cost = 0
    earned = 0
    for event in fee_events:
        if event.address == appealant_address and "UNSUCCESSFUL" in event.round_label and event.round_index == current_round_index:
            cost += event.cost
        if event.round_index == current_round_index or event.round_index == current_round_index + 1:
            earned += event.earned
    burn = cost - earned
    return burn

def compute_unsuccessful_validator_appeal_burn(current_round_index: int, appealant_address: str, fee_events: List[FeeEvent]) -> float:
    burn = 0
    cost = 0
    earned = 0
    for event in fee_events:
        if event.address == appealant_address and "UNSUCCESSFUL" in event.round_label and event.round_index == current_round_index:
            cost += event.cost
        if event.round_index == current_round_index:
            earned += event.earned
    burn = cost - earned
    return burn

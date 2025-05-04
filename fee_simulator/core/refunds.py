from typing import List
from fee_simulator.models import (
    FeeEvent,
)

def compute_sender_refund(sender_address: str, fee_events: List[FeeEvent]) -> float:
    # TODO: when introducing toppers, we need to change this function
    cost = 0
    total_paid = 0
    for event in fee_events:
        total_paid += event.earned
        if event.address == sender_address:
            cost += event.cost
    
    refund = cost - total_paid
    return refund


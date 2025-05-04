from typing import List

from fee_simulator.models import FeeEvent

def compute_current_stake(address: str, fee_events: List[FeeEvent]) -> float:
    current_stake = 0
    for event in fee_events:
        if event.address == address:
            current_stake += event.staked
            current_stake -= event.slashed
    return current_stake

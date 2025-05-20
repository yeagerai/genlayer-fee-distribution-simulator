from fee_simulator.models import FeeEvent
from typing import List
from fee_simulator.core.bond_computing import compute_appeal_bond


def compute_unsuccessful_leader_appeal_burn(
    current_round_index: int, appealant_address: str, fee_events: List[FeeEvent]
) -> float:
    burn = 0
    cost = 0
    earned = 0
    for event in fee_events:
        if (
            event.address == appealant_address
            and "UNSUCCESSFUL" in event.round_label
            and event.round_index == current_round_index
        ):
            cost += event.cost
        if (
            event.round_index == current_round_index
            or event.round_index == current_round_index + 1
        ):
            earned += event.earned
    burn = cost - earned
    return burn


def compute_unsuccessful_validator_appeal_burn(
    current_round_index: int,
    leader_timeout: int,
    validator_timeout: int,
    fee_events: List[FeeEvent],
) -> float:
    burn = 0
    cost = compute_appeal_bond(
        current_round_index - 1, leader_timeout, validator_timeout
    )
    earned = 0
    for event in fee_events:
        if (
            event.round_index == current_round_index
            and "UNSUCCESSFUL" in event.round_label
        ):
            earned += event.earned
    print(cost, earned)
    burn = cost - earned
    return burn

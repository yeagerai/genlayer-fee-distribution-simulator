import random
import string
import hashlib
from typing import List
from fee_simulator.models import (
    FeeEvent,
    TransactionBudget,
    EventSequence,
)
from fee_simulator.constants import (
    ROUND_SIZES,
    DEFAULT_STAKE,
)

def generate_random_eth_address() -> str:
    seed = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    hashed = hashlib.sha256(seed.encode()).hexdigest()
    return "0x" + hashed[:40]


def initialize_constant_stakes(
    event_sequence: EventSequence,
    addresses: List[str]
) -> List[FeeEvent]:
    events = []
    for addr in addresses:
        events.append(FeeEvent(
            sequence_id=event_sequence.next_id(),
            address=addr,
            staked=DEFAULT_STAKE,
        ))
    return events


def compute_total_cost(transaction_budget: TransactionBudget) -> int:
    if transaction_budget.appealRounds == 0:
        num_rounds = 1
    else:
        num_rounds = transaction_budget.appealRounds * 2
    total_cost = 0
    for i in range(num_rounds):
        if i % 2 == 0:
            num_rotations = transaction_budget.rotations[i // 2]
        else:
            num_rotations = 1
        total_cost += (num_rotations + 1) * (
            transaction_budget.leaderTimeout
            + ROUND_SIZES[i] * transaction_budget.validatorsTimeout
        )
    return total_cost

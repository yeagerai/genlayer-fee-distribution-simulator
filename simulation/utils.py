# simulation/utils.py

import random
import numpy as np

from simulation.config_constants import MAX_NUM_VALS, MIN_NUM_VALS
from simulation.models.enums import Vote, Role, RoundType
from simulation.models.round import Round
from simulation.models.participant import Participant


def generate_ethereum_address() -> str:
    address = "0x" + "".join(random.choices("0123456789abcdef", k=40))
    return address


def generate_validators_per_round_sequence() -> list[int]:
    sequence = [MIN_NUM_VALS]

    while sequence[-1] < MAX_NUM_VALS:
        next_number = 2 * sequence[-1] + 1
        if next_number >= MAX_NUM_VALS:
            break
        sequence.append(next_number)

    if sequence[-1] != MAX_NUM_VALS:
        sequence.append(MAX_NUM_VALS)

    return sequence


def set_random_seed(seed_value: int) -> None:
    random.seed(seed_value)
    np.random.seed(seed_value)


def compute_appeal_rounds_budget(
    leader_time_units: int, validator_time_units: int, num_rounds: int
) -> int:
    # That should take into account that appeals escalate validator count
    # and that there are three different types of appeals
    # so each type has a different cost for the user, so just with the number of rounds
    # we must compute the maximum cost so the appeal type that is most expensive

    leader_appeal_cost = ...
    validator_appeal_cost = ...
    tribunal_appeal_cost = ...

    max_cost = max(leader_appeal_cost, validator_appeal_cost, tribunal_appeal_cost)

    return num_rounds * max_cost


def compute_rotation_budget(
    leader_time_units: int, validator_time_units: int, rotations_per_round: list[int]
) -> int:
    validators_per_round = generate_validators_per_round_sequence()
    if len(rotations_per_round) != len(validators_per_round):
        raise ValueError("Rotations per round must match validators per round")
    return sum(
        rotations_per_round * validators_per_round * [validator_time_units]
    ) + sum(rotations_per_round * [leader_time_units])

def calculate_majority(voting_vector: list[Vote]) -> Vote | None:
    """Calculate the majority vote result."""
    vote_counts = {vote: 0 for vote in Vote}
    for vote in voting_vector:
        vote_counts[vote] += 1

    total_votes = len(voting_vector)
    majority_threshold = (total_votes // 2) + 1

    # Determine majority based on vote counts
    if vote_counts[Vote.DET_VIOLATION] >= majority_threshold:
        return Vote.DET_VIOLATION  # Violation takes precedence
    elif vote_counts[Vote.AGREE] >= majority_threshold:
        return Vote.AGREE  # Accept
    elif vote_counts[Vote.TIMEOUT] >= majority_threshold:
        return Vote.TIMEOUT  # Timeout
    elif vote_counts[Vote.DISAGREE] >= majority_threshold:
        return None  # Disagreement
    else:
        return None  # No clear majority
    
def get_participants_by_id(participants: dict[str, Participant], id: str) -> list[Participant]:
    return [participant for participant in participants.values() if id in participant.round_ids]

def get_leader_by_id(participants: dict[str, Participant], id: str) -> Participant:
    participants_by_id = get_participants_by_id(participants, id)
    return next((participant for participant in participants_by_id if participant.roles[id] == Role.LEADER), None)

def get_validators_by_id(participants: dict[str, Participant], id: str) -> list[Participant]:
    participants_by_id = get_participants_by_id(participants, id)
    return [participant for participant in participants_by_id if participant.roles[id] == Role.VALIDATOR]

def get_appealants_by_id(participants: dict[str, Participant], id: str) -> list[Participant]:
    participants_by_id = get_participants_by_id(participants, id)
    return [participant for participant in participants_by_id if participant.roles[id] == Role.APPEALANT]

def move_rewards_from_participant(round_id: str, amount: int, participant: Participant, to_participant: Participant) -> None:
    participant.rewards[round_id] -= amount
    to_participant.rewards[round_id] += amount

def compute_next_step(round: Round) -> RoundType | None:
    current_result = round.result
    next_step = None
    # logic for next step
    return next_step

def should_finalize(round: Round) -> bool: ...

def select_leader_and_validators(participants: dict[str, Participant], previous_round_ids: str) -> tuple[str, list[str]]: 
    ...
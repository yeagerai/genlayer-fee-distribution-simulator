# simulation/utils.py

import random

from simulation.config_constants import MAX_NUM_VALS, MIN_NUM_VALS
from simulation.models.enums import Vote, Role, RoundType


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
    # np.random.seed(seed_value)


def compute_appeal_rounds_budget(
    leader_time_units: int, validator_time_units: int, num_rounds: int
) -> int:
    # TODO: fix this
    validators_per_round = generate_validators_per_round_sequence()
    leader_appeal_cost = sum(leader_time_units + validators_per_round[round_number] * validator_time_units for round_number in range(num_rounds))
    validator_appeal_cost = sum(validators_per_round[round_number] * validator_time_units for round_number in range(num_rounds))
    tribunal_appeal_cost = 0

    max_cost = max(leader_appeal_cost, validator_appeal_cost, tribunal_appeal_cost)

    return max_cost


def compute_rotation_budget(
    leader_time_units: int, 
    validator_time_units: int, 
    rotations_per_round: list[int]
) -> int:
    validators_per_round = generate_validators_per_round_sequence()
    if len(rotations_per_round) != len(validators_per_round):
        raise ValueError("Rotations per round must match validators per round")
    
    # Calculate validator costs
    validator_costs = sum(
        rotations * num_validators * validator_time_units
        for rotations, num_validators in zip(rotations_per_round, validators_per_round)
    )
    
    # Calculate leader costs
    leader_costs = sum(
        rotations * leader_time_units
        for rotations in rotations_per_round
    )
    
    return validator_costs + leader_costs

def calculate_majority(voting_vector: list[Vote]) -> Vote | None:
    """Calculate the majority vote result."""
    vote_counts = {vote: 0 for vote in Vote}
    for vote in voting_vector.values():
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

def select_leader_and_validators(round_number: int, participants: dict, round_id: str) -> tuple[str, list[str]]:
    # Get sequence of required validators per round
    validators_per_round = generate_validators_per_round_sequence()
    required_validators = validators_per_round[round_number]
    
    # Get available participants (those who haven't participated in this round)
    available_participants = [
        p_id for p_id, p in participants.items() 
        if p.rounds == {}
    ]
    if len(available_participants) < required_validators:  # +1 for leader
        raise ValueError(f"Not enough available participants for round {round_number}")
    
    # Randomly select leader and validators
    selected_participants = random.sample(available_participants, required_validators)
    leader_id = selected_participants[0]
    validator_ids = selected_participants
    
    # Assign roles to participants
    participants[leader_id].add_to_round(round_id, Role.LEADER)
    for validator_id in validator_ids:
        participants[validator_id].add_to_round(round_id, Role.VALIDATOR)
    
    return leader_id, validator_ids

def compute_next_step(round):
    if not round.majority:
        return RoundType.ROTATE

def should_finalize(round):
    ...

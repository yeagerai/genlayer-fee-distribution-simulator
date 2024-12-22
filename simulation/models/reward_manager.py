from simulation.models.budget import Budget
from simulation.models.participant import Participant
from simulation.models.enums import RoundType, RewardType
from simulation.errors import OutOfGasError


class RewardManager:
    def __init__(self, budget: Budget, initial_validator_pool: dict[str, Participant]):
        self.budget = budget
        self.initial_validator_pool = initial_validator_pool

    def move_rewards_from_participant(self, 
                                      amount: int, 
                                      from_round_id: str,
                                      to_round_id: str,
                                      from_participant_id: str, 
                                      to_participant_id: str) -> None:
        if self.initial_validator_pool[from_participant_id].rounds[from_round_id].reward - amount < 0:
            raise OutOfGasError(f"Not enough gas to spend for move rewards from {from_participant_id} to {to_participant_id}")
        self.initial_validator_pool[from_participant_id].rounds[to_round_id].reward -= amount
        self.initial_validator_pool[to_participant_id].rounds[to_round_id].reward += amount

    def add_rewards_to_participant(self, reward_type: RewardType, round_id: str, participant_id: str, round_type: RoundType, round_number: int, amount: int | None = None) -> None:
        self.budget.spend_round_budget(round_id, round_type, round_number)
        if reward_type == RewardType.LEADER:
            self.initial_validator_pool[participant_id].rounds[round_id].reward += self.budget.leader_time_units
        elif reward_type == RewardType.VALIDATOR:
            self.initial_validator_pool[participant_id].rounds[round_id].reward += self.budget.validator_time_units
        
        if amount is not None and reward_type == RewardType.APPEALANT:
            self.initial_validator_pool[participant_id].rounds[round_id].reward += amount


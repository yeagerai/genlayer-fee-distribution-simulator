from simulation.models.budget import Budget
from simulation.models.participant import Participant
from simulation.models.enums import RoundType, RewardType, Vote, LeaderResult
from simulation.errors import OutOfGasError
from simulation.config_constants import LEADER_IDLE_SLASHING_PERCENTAGE, VALIDATOR_IDLE_SLASHING_PERCENTAGE


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

    def add_rewards_to_participant(self, reward_type: RewardType|None, participant_output: Vote | LeaderResult | None, round_id: str, participant_id: str, round_type: RoundType, round_number: int, amount: int | None = None) -> None:
        if amount is not None:
            self.initial_validator_pool[participant_id].rounds[round_id].reward += amount
            return
        if reward_type == RewardType.LEADER:
            if participant_output == LeaderResult.RECEIPT:
                self.initial_validator_pool[participant_id].rounds[round_id].reward += self.budget.leader_time_units
            elif participant_output == LeaderResult.TIMEOUT:
                self.initial_validator_pool[participant_id].rounds[round_id].reward += self.budget.leader_time_units * 0.5
            elif participant_output == LeaderResult.IDLE:
                self.initial_validator_pool[participant_id].rounds[round_id].reward -= self.initial_validator_pool[participant_id].stake * (1-LEADER_IDLE_SLASHING_PERCENTAGE)
        elif reward_type == RewardType.VALIDATOR:
            if participant_output == Vote.IDLE:
                self.initial_validator_pool[participant_id].rounds[round_id].reward -= self.initial_validator_pool[participant_id].stake * (1-VALIDATOR_IDLE_SLASHING_PERCENTAGE)
            else:
                self.initial_validator_pool[participant_id].rounds[round_id].reward += self.budget.validator_time_units


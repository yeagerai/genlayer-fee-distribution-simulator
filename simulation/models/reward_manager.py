from simulation.models.budget import Budget
from simulation.models.participant import Participant


class RewardManager:
    def __init__(self, budget: Budget, initial_validator_pool: dict[str, Participant]):
        self.budget = budget
        self.initial_validator_pool = initial_validator_pool

    def move_rewards_from_participant(self, 
                                      amount: int, 
                                      to_round_id: str,
                                      from_participant_id: str, 
                                      to_participant_id: str) -> None:
        self.initial_validator_pool[from_participant_id].rewards[to_round_id] -= amount
        self.initial_validator_pool[to_participant_id].rewards[to_round_id] += amount

    def add_rewards_to_participant(self, amount: int, round_id: str, participant_id: str) -> None:
        # take budget into account
        self.initial_validator_pool[participant_id].rewards[round_id] += amount


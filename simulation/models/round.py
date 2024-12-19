# simulation/models/round.py

from datetime import datetime, timedelta

from simulation.config_constants import FINALITY_WINDOW_MINS
from simulation.models.enums import Vote, AppealType, LeaderResult, Role
from simulation.utils import generate_ethereum_address, calculate_majority
from simulation.models.reward_manager import RewardManager

class Round:
    def __init__(
        self,
        round_number: int,
        reward_manager: RewardManager,
        leader_result: LeaderResult | None = None,
        voting_vector: list[Vote] | None = None,
    ):
        self.id = generate_ethereum_address()
        self.round_number = round_number
        self.leader_result = leader_result
        self.voting_vector = voting_vector
        self.leader_id, self.validator_ids = reward_manager.validators_and_leader_selection(self.id)
        self.majority = calculate_majority(self.voting_vector)


class InitialRound(Round):
    def __init__(self, round_number: int, reward_manager: RewardManager, *args, **kwargs):
        super().__init__(round_number, reward_manager, *args, **kwargs)
        self.distribute_rewards(reward_manager)

    def distribute_rewards(self, reward_manager: RewardManager): ...

class RotationRound(Round):
    def __init__(self, round_number: int, reward_manager: RewardManager, *args, **kwargs):
        super().__init__(round_number, reward_manager, *args, **kwargs)
        self.distribute_rewards(reward_manager)

    def distribute_rewards(self, reward_manager: RewardManager): ...

class LeaderAppealRound(Round):
    def __init__(self, round_number: int, reward_manager: RewardManager, *args, **kwargs):
        super().__init__(round_number, reward_manager, *args, **kwargs)
        self.distribute_rewards(reward_manager)

    @property
    def successful(self):
        return self.compute_success()
    
    def compute_success(self): ...

    def distribute_rewards(self, reward_manager: RewardManager): ...

class ValidatorAppealRound(Round):
    def __init__(self, round_number: int, reward_manager: RewardManager, *args, **kwargs):
        super().__init__(round_number, reward_manager, *args, **kwargs)
        self.distribute_rewards(reward_manager)

    @property
    def successful(self):
        return self.compute_success()
    
    def compute_success(self): ...

    def distribute_rewards(self, reward_manager: RewardManager): ...

class TribunalAppealRound(Round):
    def __init__(self, round_number: int, reward_manager: RewardManager, *args, **kwargs):
        super().__init__(round_number, reward_manager, *args, **kwargs)
        self.distribute_rewards(reward_manager)

    @property
    def successful(self):
        return self.compute_success()
    
    def compute_success(self): ...

    def distribute_rewards(self, reward_manager: RewardManager): ...

# simulation/models/round.py

from datetime import datetime, timedelta

from simulation.config_constants import FINALITY_WINDOW_MINS
from simulation.models.enums import Vote, AppealType, LeaderResult, RoundType, RewardType
from simulation.utils import generate_ethereum_address, calculate_majority, select_leader_and_validators
from simulation.models.reward_manager import RewardManager

def spend_budget_before_rewards(func):
    """Decorator that ensures budget is spent before rewards are distributed."""
    def wrapper(self, reward_manager: RewardManager, *args, **kwargs):
        # Spend budget for the round
        reward_manager.budget.spend_round_budget(self.id, self.type, self.round_number)
        # Then distribute rewards
        return func(self, reward_manager, *args, **kwargs)
    return wrapper

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
        self.leader_id, self.validator_ids = select_leader_and_validators(self.round_number, reward_manager.initial_validator_pool, self.id)
        self.voting_vector = {participant_id: vote for participant_id, vote in zip(self.validator_ids, voting_vector)}
        self.majority = calculate_majority(self.voting_vector)


class InitialRound(Round):
    def __init__(self, round_number: int, reward_manager: RewardManager, *args, **kwargs):
        super().__init__(round_number, reward_manager, *args, **kwargs)
        self.type = RoundType.INITIAL
        self.distribute_rewards(reward_manager)

    @spend_budget_before_rewards
    def distribute_rewards(self, reward_manager: RewardManager):
        if self.majority:
            for participant_id in self.validator_ids:
                if self.voting_vector[participant_id] == self.majority:
                    reward_manager.add_rewards_to_participant(
                        reward_type=RewardType.VALIDATOR,
                        participant_output=self.majority,
                        round_number=self.round_number,
                        round_id=self.id,
                        participant_id=participant_id,
                        round_type=self.type
                    )
        else:
            for participant_id in self.validator_ids:
                reward_manager.add_rewards_to_participant(
                    reward_type=RewardType.VALIDATOR,
                    participant_output=None,
                    round_number=self.round_number,
                    round_id=self.id,
                    participant_id=participant_id,
                    round_type=self.type
                )

        reward_manager.add_rewards_to_participant(
            reward_type=RewardType.LEADER,
            participant_output=self.leader_result,
            round_number=self.round_number,
            round_id=self.id,
            participant_id=self.leader_id,
            round_type=self.type
        )
        
class RotationRound(Round):
    def __init__(self, round_number: int, reward_manager: RewardManager, *args, **kwargs):
        super().__init__(round_number, reward_manager, *args, **kwargs)
        self.type = RoundType.ROTATE

        self.distribute_rewards(reward_manager)

    @spend_budget_before_rewards
    def distribute_rewards(self, reward_manager: RewardManager): ...

class LeaderAppealRound(Round):
    def __init__(self, round_number: int, reward_manager: RewardManager, *args, **kwargs):
        super().__init__(round_number, reward_manager, *args, **kwargs)
        self.type = AppealType.LEADER
        self.distribute_rewards(reward_manager)

    @property
    def successful(self, previous_round: Round):
        return self.compute_success(previous_round)
    
    def compute_success(self, previous_round: Round): return self.majority != previous_round.majority

    @spend_budget_before_rewards
    def distribute_rewards(self, reward_manager: RewardManager): ...

class ValidatorAppealRound(Round):
    def __init__(self, round_number: int, reward_manager: RewardManager, *args, **kwargs):
        super().__init__(round_number, reward_manager, *args, **kwargs)
        self.type = AppealType.VALIDATOR
        self.distribute_rewards(reward_manager)

    @property
    def successful(self):
        return self.compute_success()
    
    def compute_success(self): ...

    @spend_budget_before_rewards
    def distribute_rewards(self, reward_manager: RewardManager): ...

class TribunalAppealRound(Round):
    def __init__(self, round_number: int, reward_manager: RewardManager, *args, **kwargs):
        super().__init__(round_number, reward_manager, *args, **kwargs)
        self.type = AppealType.TRIBUNAL
        self.distribute_rewards(reward_manager)

    @property
    def successful(self):
        return self.compute_success()
    
    def compute_success(self): ...

    @spend_budget_before_rewards
    def distribute_rewards(self, reward_manager: RewardManager): ...

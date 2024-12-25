# simulation/models/optimistic_transaction.py

from simulation.utils import generate_ethereum_address
from simulation.models.budget import Budget
from simulation.models.round import InitialRound, RotationRound, Round, LeaderAppealRound, ValidatorAppealRound, TribunalAppealRound
from simulation.models.enums import AppealType, Vote, Status, LeaderResult, RoundType
from simulation.models.participant import Participant
from simulation.models.reward_manager import RewardManager
from simulation.utils import compute_next_step, should_finalize, generate_validators_per_round_sequence

def compute_next_step_after(func):
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.automatic_next_step = compute_next_step(self.rounds[-1])
        self.status = Status.FINAL if should_finalize(self.rounds[-1]) else Status.NONFINAL
        return result
    return wrapper

class Transaction:
    def __init__(
        self,
        budget: Budget,
        initial_validator_pool: dict[str, Participant],
    ):

        self.id = generate_ethereum_address()
        self.reward_manager = RewardManager(budget, initial_validator_pool) # TODO: load from old state
        self.num_vals_per_round = generate_validators_per_round_sequence()
        self.rounds: list[Round] = []
        self.status = Status.NONFINAL
        self.automatic_next_step = None

    @compute_next_step_after
    def start(self, leader_result: str, voting_vector: list[Vote]) -> None:
        if len(self.rounds) > 0:
            raise ValueError("Transaction already started")
        if len(voting_vector) != self.num_vals_per_round[0]:
            raise ValueError("Invalid voting vector length")

        first_round = InitialRound(
            round_number=0,
            reward_manager=self.reward_manager,
            leader_result=leader_result,
            voting_vector=voting_vector,
        )
        self.rounds.append(first_round)

    @property
    def final(self):
        return self.status == Status.FINAL   
    
    @compute_next_step_after
    def rotate(
        self, 
        leader_result: LeaderResult, 
        voting_vector: list[Vote]
    ) -> None:
        if self.final:
            raise ValueError("Transaction is final, cannot add new rounds")
        
        if len(voting_vector) != self.num_vals_per_round[len(self.rounds)]:
            raise ValueError("Invalid voting vector length")

        if self.automatic_next_step != RoundType.ROTATE:
            raise ValueError("Transaction is not in rotate state")

        new_round = RotationRound(
            round_number=len(self.rounds),
            reward_manager=self.reward_manager,
            leader_result=leader_result,
            voting_vector=voting_vector,
        )
        
        self.rounds.append(new_round)

    
    @compute_next_step_after
    def appeal(self, appealant_id: str, appeal_type: AppealType, bond: int, leader_result: LeaderResult, voting_vector: list[Vote]) -> None:
        if self.final:
            raise ValueError("Transaction is final, cannot appeal")

        if len(voting_vector) != self.num_vals_per_round[len(self.rounds)]:
            raise ValueError("Invalid voting vector length")

        if self.automatic_next_step != RoundType.APPEAL:
            raise ValueError("Transaction is not in appeal state")

        appeal_cls = {
            AppealType.LEADER: LeaderAppealRound,
            AppealType.VALIDATOR: ValidatorAppealRound,
            AppealType.TRIBUNAL: TribunalAppealRound
        }[appeal_type]

        new_round = appeal_cls(
            round_number=len(self.rounds),
            bond=bond,
            appealant_id=appealant_id,
            reward_manager=self.reward_manager,
            leader_result=leader_result,
            voting_vector=voting_vector,
        )
        self.rounds.append(new_round)

    def print_current_rewards(self):
        """Print current reward distribution for all participants."""
        for round in self.rounds:
            print(f"\nRound {round.round_number} (ID: {round.id}):")
            
            # Print leader rewards
            leader_reward = self.reward_manager.initial_validator_pool[round.leader_id].rounds[round.id].reward
            print(f"  Leader {round.leader_id}: {leader_reward}")
            
            # Print validator rewards
            for validator_id in round.validator_ids:
                reward = self.reward_manager.initial_validator_pool[validator_id].rounds[round.id].reward
                print(f"  Validator {validator_id}: {reward}")

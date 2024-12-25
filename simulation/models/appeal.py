# simulation/models/appeal.py

from simulation.utils import (
    generate_ethereum_address, 
    calculate_majority, 
    generate_validators_per_round_sequence, 
    get_participants_by_id, 
    get_leader_by_id,
    move_rewards_from_participant
)
from simulation.models.enums import AppealType, LeaderResult, Role, Vote
from simulation.models.participant import Participant


class Appeal:
    def __init__(
        self,
        current_round_id: str,
        current_round_result: Vote | None,
        appealant_id: str,
        appeal_type: AppealType,
        bond: int,
        leader_result: LeaderResult | None,
        voting_vector: list[str] | None = None,
        initial_validator_pool: dict[str, Participant] | None = None,
    ):
        self.current_round_id = current_round_id
        self.current_round_result = current_round_result
        self.id = generate_ethereum_address()
        self.bond = bond
        self.voting_vector = voting_vector or []
        self.leader_result = leader_result
        self.appealant_id = appealant_id
        self.appeal_type = appeal_type
        self.initial_validator_pool = initial_validator_pool
        self.successful = False
        self.appealant_reward = 0
        
        # Will be set by child classes
        self.participants_ids: list[str] = []
        self.leader_id: str | None = None
        
        self.execute()

class LeaderAppeal(Appeal):

    def select_participants(self) -> None:
        if not self.initial_validator_pool:
            raise ValueError("No validator pool provided for leader appeal")

        vals_sequence = generate_validators_per_round_sequence()
        # Get current participants and leader
        current_participants = get_participants_by_id(self.initial_validator_pool, self.current_round_id)
        current_participants_ids = [p.id for p in current_participants]
        current_leader = get_leader_by_id(self.initial_validator_pool, self.current_round_id)
        num_needed = next(vals_sequence[:] == len(current_participants))
        # Create available validator pool (excluding current participants)
        available_validators_ids = [
            v.id for v in self.initial_validator_pool.values()
            if v.id not in current_participants_ids
        ]
        if not available_validators_ids:
            raise ValueError("Not enough validators in pool for leader appeal")
        if len(available_validators_ids) < num_needed:
            raise ValueError(f"Not enough validators in pool. Need {num_needed}, have {len(available_validators_ids)}")



        # Select new leader (first available validator)
        self.leader_id = available_validators_ids[0]
        self.initial_validator_pool[self.leader_id].assign_role(self.id, Role.LEADER)

        for id in available_validators_ids[1:num_needed+1]:
            if id != current_leader.id:
                self.initial_validator_pool[id].assign_role(self.id, Role.VALIDATOR)

    def calculate_result(self) -> Vote | None:
        new_majority = calculate_majority(self.voting_vector)                
        if new_majority != self.current_round_result:
            self.successful = True
            return new_majority
        else:
            self.successful = False
            return None

    def distribute_rewards(self):
        leader_id = get_leader_by_id(self.initial_validator_pool, self.current_round_id).id
        if self.successful:
            # Successful appeal:
            # - Appealant gets old leader's stake + bond
            self.initial_validator_pool[self.appealant_id].rewards[self.id]+=self.bond
            old_quantity = self.initial_validator_pool[leader_id].rewards[self.current_round_id]
            move_rewards_from_participant(self.id, 
                                          old_quantity, 
                                          self.initial_validator_pool[leader_id], 
                                          self.initial_validator_pool[self.appealant_id])
            
            # Old validators split remaining budget
            remaining_budget = sum(p.get_total_rewards() for p in self.participants)
            per_validator = remaining_budget // len(self.participants)
            for validator in self.participants:
                validator.add_reward(self.id, per_validator)
        else:
            # Unsuccessful appeal:
            # - Bond is split among validators
            self.initial_validator_pool[self.appealant_id].rewards[self.id]-=self.bond
            per_validator = self.bond // len(self.participants)
            for validator in self.participants:
                validator.add_reward(self.id, per_validator)

class ValidatorAppeal(Appeal):
    def select_participants(self) -> None:
        if not self.initial_validator_pool:
            raise ValueError("No validator pool provided for validator appeal")

        # Keep track of current participants
        current_participants = set(p.id for p in self.participants)
        if self.leader:
            current_participants.add(self.leader.id)

        # Create available validator pool (excluding current participants)
        available_validators = [
            v for v in self.initial_validator_pool.values()
            if v.id not in current_participants
        ]

        # Calculate number of additional validators needed (N+1)
        num_additional = (len(self.participants) // 2) + 1

        if len(available_validators) < num_additional:
            raise ValueError(f"Not enough validators in pool. Need {num_additional}, have {len(available_validators)}")

        # Add new validators to existing participants
        new_validators = available_validators[:num_additional]
        self.participants.extend(new_validators)

        # Assign roles to new validators
        for validator in new_validators:
            validator.assign_role(self.id, Role.VALIDATOR)

    def calculate_result(self) -> bool:
        # Get N+1 more validators
        num_new_validators = (len(self.voting_vector) // 2) + 1
        majority_threshold = (num_new_validators // 2) + 1
        
        # Count votes from new validators only
        new_votes = self.voting_vector[-num_new_validators:]
        vote_counts = {"A": 0, "D": 0, "T": 0, "I": 0, "V": 0}
        for vote in new_votes:
            vote_counts[vote] += 1
            
        # Determine if new validators have different majority
        new_majority = None
        for vote_type, count in vote_counts.items():
            if count >= majority_threshold:
                new_majority = vote_type
                break
                
        return new_majority is not None and new_majority != self.leader_result

    def distribute_rewards(self):
        if self.successful:
            # Successful appeal:
            # - Appealant gets old leader's stake + bond
            self.appealant.add_reward(self.id, self.bond + self.leader.get_total_rewards())
            
            # Old majority validators pay new majority validators
            old_validators_reward = sum(p.get_total_rewards() for p in self.participants[:-len(self.voting_vector)])
            new_validators = self.participants[-len(self.voting_vector):]
            per_validator = old_validators_reward // len(new_validators)
            
            for validator in new_validators:
                validator.add_reward(self.id, per_validator)
        else:
            # Unsuccessful appeal:
            # - Bond goes to gas for new validators
            num_new_validators = (len(self.voting_vector) // 2) + 1
            per_validator = self.bond // num_new_validators
            
            for validator in self.participants[-num_new_validators:]:
                validator.add_reward(self.id, per_validator)

class TribunalAppeal(Appeal):
    def select_participants(self) -> None:
        if not self.initial_validator_pool:
            raise ValueError("No validator pool provided for tribunal appeal")

        # Keep track of current participants
        current_participants = set(p.id for p in self.participants)
        if self.leader:
            current_participants.add(self.leader.id)

        # Create available validator pool (excluding current participants)
        available_validators = [
            v for v in self.initial_validator_pool.values()
            if v.id not in current_participants
        ]

        # Calculate number of tribunal validators needed (N+1)
        num_tribunal = (len(self.participants) // 2) + 1

        if len(available_validators) < num_tribunal:
            raise ValueError(f"Not enough validators in pool. Need {num_tribunal}, have {len(available_validators)}")

        # Add tribunal validators to existing participants
        tribunal_validators = available_validators[:num_tribunal]
        self.participants.extend(tribunal_validators)

        # Assign roles to tribunal validators
        for validator in tribunal_validators:
            validator.assign_role(self.id, Role.VALIDATOR)
    
    def calculate_result(self) -> bool:
        # Simple majority check for deterministic violation
        num_validators = len(self.voting_vector)
        majority_threshold = (num_validators // 2) + 1
        
        violation_votes = sum(1 for vote in self.voting_vector if vote == "V")
        return violation_votes >= majority_threshold

    def distribute_rewards(self):
        # No rewards or bonds in tribunal appeals
        pass
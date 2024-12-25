# simulation/transaction_budget.py


from dataclasses import dataclass

from simulation.errors import OutOfGasError
from simulation.utils import (
    generate_validators_per_round_sequence,
    compute_appeal_rounds_budget,
    compute_rotation_budget,
)

from simulation.models.enums import RoundType, AppealType


class Budget:
    def __init__(
        self,
        leader_time_units: int,
        validator_time_units: int,
        rotations_per_round: list[int],
        appeal_rounds: int,
        total_internal_messages_budget: int = 0,
        external_messages_budget: int = 0,
    ):
        # Validate budget lists
        self.validators_per_round = generate_validators_per_round_sequence()
        num_possible_rounds = len(self.validators_per_round)
        if len(rotations_per_round) != num_possible_rounds:
            raise ValueError(f"Rotation budgets must have length {num_possible_rounds}")

        # Direct budgets
        self.leader_time_units = leader_time_units
        self.validator_time_units = validator_time_units
        self.initial_round_budget = leader_time_units + validator_time_units*self.validators_per_round[0]
        self.rotation_budget = compute_rotation_budget(
            leader_time_units=leader_time_units,
            validator_time_units=validator_time_units,
            rotations_per_round=rotations_per_round,
        )
        self.appeal_rounds_budget = compute_appeal_rounds_budget(
            leader_time_units=leader_time_units,
            validator_time_units=validator_time_units,
            num_rounds=appeal_rounds,
        )

        # Message budgets
        self.total_internal_messages_budget = total_internal_messages_budget
        self.external_messages_budget = external_messages_budget

    def spend_round_budget(self, round_id: str, round_type: RoundType | AppealType, num_rounds: int) -> None:
        cost = self.leader_time_units + self.validator_time_units*self.validators_per_round[num_rounds]
        if round_type == RoundType.INITIAL:  
            self.initial_round_budget -= cost
            if self.initial_round_budget < 0:
                raise OutOfGasError(f"Not enough gas to spend for initial round {round_id}")
        elif round_type == RoundType.ROTATE:
            self.rotation_budget -= cost
            if self.rotation_budget < 0:
                raise OutOfGasError(f"Not enough gas to spend for rotate round {round_id}")
        else:
            if round_type == AppealType.LEADER:
                self.appeal_rounds_budget -= cost
                if self.appeal_rounds_budget < 0:
                    raise OutOfGasError(f"Not enough gas to spend for appeal leader round {round_id}")
            elif round_type == AppealType.VALIDATOR:
                self.appeal_rounds_budget -= cost
                if self.appeal_rounds_budget < 0:
                    raise OutOfGasError(f"Not enough gas to spend for appeal validator round {round_id}")
            elif round_type == AppealType.TRIBUNAL:
                self.appeal_rounds_budget -= cost
                if self.appeal_rounds_budget < 0:
                    raise OutOfGasError(f"Not enough gas to spend for appeal tribunal round {round_id}")

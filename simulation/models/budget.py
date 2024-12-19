# simulation/transaction_budget.py


from dataclasses import dataclass

from simulation.errors import OutOfGasError
from simulation.utils import (
    generate_validators_per_round_sequence,
    compute_appeal_rounds_budget,
    compute_rotation_budget,
)

from simulation.models.round import Round


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
        validators_per_round = generate_validators_per_round_sequence()
        num_possible_rounds = len(validators_per_round)
        if len(rotations_per_round) != num_possible_rounds:
            raise ValueError(f"Rotation budgets must have length {num_possible_rounds}")

        # Direct budgets
        self.leader_time_units = leader_time_units
        self.validator_time_units = validator_time_units
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

        # Calculate total available gas
        self.total_gas = (
            self.leader_time_units
            + self.validator_time_units
            + self.rotation_budget
            + self.appeal_rounds_budget
            + self.total_internal_messages_budget
            + self.external_messages_budget
        )

        # Runtime tracking
        self.remaining_gas = self.total_gas
        self.failed = False

    def spend_round_budget(self, round: Round) -> None:
        num_validators = len(round.validator_ids)
        self.remaining_gas -= self.validator_time_units * num_validators
        self.remaining_gas -= self.leader_time_units
        self.remaining_gas -= self.total_internal_messages_budget
        self.remaining_gas -= self.external_messages_budget

        if self.remaining_gas < 0:
            raise OutOfGasError(f"Not enough gas to spend for round {round.round_number}")


    def __repr__(self) -> str:
        """String representation of the budget state."""
        used, remaining, percentage = self.get_gas_usage()
        return (
            f"TransactionBudget("
            f"used={used}, "
            f"remaining={remaining}, "
            f"usage={percentage:.1f}%, "
            f"failed={self.failed})"
        )

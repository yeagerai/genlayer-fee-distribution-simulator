from dataclasses import dataclass

@dataclass
class PresetLeaf:
    """
    A leaf preset representing a simple message pattern with direct gas costs.

    Used for basic message patterns that don't reference other messages.
    Gas costs are fixed and known at initialization.
    """

    leader_time_units: int = 0
    validator_time_units: int = 0
    rotation_budget: list[int] = None
    appeal_rounds_budget: int = None

    def compute_total_gas(self) -> int:
        """
        Calculate total gas required for this leaf preset.

        Returns:
            int: Sum of all gas costs in this preset
        """
        return (
            self.leader_time_units
            + self.validator_time_units
            + sum(self.rotation_budget)
            + self.appeal_rounds_budget
        )


@dataclass
class PresetBranch:
    """
    A branch preset representing a complex message pattern that may reference other presets.

    Used for composite message patterns that can reference other branches or leaves.
    Includes both direct gas costs and references to other message patterns.
    """

    leader_time_units: int = 0
    validator_time_units: int = 0
    rotation_budget: list[int] = None
    appeal_rounds_budget: int = None
    internal_messages_budget_guess: dict[str, str] = (
        None  # message_key -> reference_key
    )
    external_messages_budget_guess: list[int] = None

    def compute_own_gas(self) -> int:
        """
        Calculate gas required for this branch's own operations.

        Returns:
            int: Sum of direct gas costs (excluding referenced messages)
        """
        return (
            self.leader_time_units
            + self.validator_time_units
            + sum(self.rotation_budget)
            + self.appeal_rounds_budget
            + sum(self.external_messages_budget_guess)
        )
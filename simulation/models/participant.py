# simulation/models/participant.py

"""
Participant module for the OptDem consensus simulation.

This module defines the Participant class, which represents an actor in the OptDem consensus
mechanism. Participants can take different roles (leader, validator, or appealant) in
different rounds or appeals, and accumulate rewards (positive) or penalties (negative)
from their participation.
"""

from simulation.utils import generate_ethereum_address
from simulation.models.enums import Role


class Participant:
    """
    A participant in the OptDem consensus mechanism.

    Each participant has a unique identifier and can take different roles in different
    rounds or appeals. They accumulate rewards or penalties based on their actions
    and the consensus outcomes.

    Attributes:
        id (str): Unique identifier for the participant (Ethereum address format)
        roles (dict[str, Role]): Mapping of round/appeal IDs to roles
        rewards (dict[str, int]): Mapping of round/appeal IDs to rewards/penalties
    """

    def __init__(self, id: str | None = None, role: Role | None = None):
        """
        Initialize a new participant.

        Args:
            id (str, optional): Unique identifier. If None, generates a random address
            role (Role, optional): Initial role of the participant
        """
        self.id = id if id else generate_ethereum_address()
        self.roles: dict[str, Role] = {}
        self.rewards: dict[str, int] = {}

    def assign_role(self, context_id: str, role: Role) -> None:
        """
        Assign a role to the participant for a specific round or appeal.

        Args:
            context_id (str): ID of the round or appeal
            role (Role): Role to assign (LEADER, VALIDATOR, or APPEALANT)
        """
        self.roles[context_id] = role

    def add_reward(self, context_id: str, amount: int) -> None:
        """
        Add a reward or penalty for a specific round or appeal.

        Args:
            context_id (str): ID of the round or appeal
            amount (int): Amount to add (positive for rewards, negative for penalties)
        """
        if context_id in self.rewards:
            self.rewards[context_id] += amount
        else:
            self.rewards[context_id] = amount

    def get_total_rewards(self) -> int:
        """
        Calculate total rewards/penalties across all rounds and appeals.

        Returns:
            int: Sum of all rewards (positive) and penalties (negative)
        """
        return sum(self.rewards.values())

    def get_role_in_context(self, context_id: str) -> Role | None:
        """
        Get the participant's role in a specific round or appeal.

        Args:
            context_id (str): ID of the round or appeal

        Returns:
            Role | None: The role in the given context, or None if not participating
        """
        return self.roles.get(context_id)

    def __repr__(self) -> str:
        """String representation of the Participant."""
        return f"Participant(id={self.id}, roles={len(self.roles)}, total_rewards={self.get_total_rewards()})"

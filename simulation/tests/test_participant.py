import pytest
from simulation.models.participant import Participant
from simulation.models.enums import Role


def test_participant_initialization():
    # Test with provided ID
    p1 = Participant(id="0x123", role=Role.VALIDATOR)
    assert p1.id == "0x123"

    # Test with auto-generated ID
    p2 = Participant()
    assert p2.id.startswith("0x")
    assert len(p2.id) == 42  # Standard Ethereum address length


def test_role_assignment():
    p = Participant()
    round_id = "round_1"

    p.assign_role(round_id, Role.LEADER)
    assert p.get_role_in_context(round_id) == Role.LEADER

    # Test role reassignment
    p.assign_role(round_id, Role.VALIDATOR)
    assert p.get_role_in_context(round_id) == Role.VALIDATOR


def test_rewards():
    p = Participant()
    round_id = "round_1"
    appeal_id = "appeal_1"

    # Test adding rewards
    p.add_reward(round_id, 100)
    assert p.rewards[round_id] == 100

    # Test adding penalties
    p.add_reward(appeal_id, -50)
    assert p.rewards[appeal_id] == -50

    # Test cumulative rewards
    assert p.get_total_rewards() == 50

    # Test adding to existing reward
    p.add_reward(round_id, 50)
    assert p.rewards[round_id] == 150
    assert p.get_total_rewards() == 100


def test_multiple_roles():
    p = Participant()

    # Test multiple roles in different contexts
    p.assign_role("round_1", Role.VALIDATOR)
    p.assign_role("round_2", Role.LEADER)
    p.assign_role("appeal_1", Role.APPEALANT)

    assert p.get_role_in_context("round_1") == Role.VALIDATOR
    assert p.get_role_in_context("round_2") == Role.LEADER
    assert p.get_role_in_context("appeal_1") == Role.APPEALANT
    assert p.get_role_in_context("nonexistent") is None

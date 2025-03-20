import pytest
from simulation.models.participant import Participant, RoundData
from simulation.models.enums import Role
from simulation.utils import generate_ethereum_address


def test_participant_initialization():
    """Test participant initialization with and without ID."""
    # Test with provided ID
    provided_id = generate_ethereum_address()
    p1 = Participant(id=provided_id)
    assert p1.id == provided_id
    assert isinstance(p1.rounds, dict)
    assert len(p1.rounds) == 0

    # Test with auto-generated ID
    p2 = Participant()
    assert p2.id.startswith("0x")
    assert len(p2.id) == 42  # Standard Ethereum address length
    assert isinstance(p2.rounds, dict)
    assert len(p2.rounds) == 0


def test_add_to_round():
    """Test adding participant to a round with a specific role."""
    p = Participant()
    round_id = generate_ethereum_address()
    
    # Add participant to round as validator
    p.add_to_round(round_id, Role.VALIDATOR)
    
    # Verify round data
    assert round_id in p.rounds
    assert isinstance(p.rounds[round_id], RoundData)
    assert p.rounds[round_id].id == round_id
    assert p.rounds[round_id].role == Role.VALIDATOR
    assert p.rounds[round_id].reward == 0


def test_get_role_in_round():
    """Test retrieving participant's role in a specific round."""
    p = Participant()
    round_id = generate_ethereum_address()
    
    # Add participant to round
    p.add_to_round(round_id, Role.LEADER)
    
    # Test role retrieval
    assert p.get_role_in_round(round_id) == Role.LEADER
    
    # Test nonexistent round
    with pytest.raises(KeyError):
        p.get_role_in_round(generate_ethereum_address())


def test_multiple_rounds():
    """Test participant involvement in multiple rounds."""
    p = Participant()
    
    # Add participant to multiple rounds with different roles
    rounds_data = [
        (generate_ethereum_address(), Role.VALIDATOR),
        (generate_ethereum_address(), Role.LEADER),
        (generate_ethereum_address(), Role.APPEALANT)
    ]
    
    for round_id, role in rounds_data:
        p.add_to_round(round_id, role)
    
    # Verify all rounds were added
    assert len(p.rounds) == len(rounds_data)
    
    # Verify roles in each round
    for round_id, role in rounds_data:
        assert p.get_role_in_round(round_id) == role


def test_rewards_calculation():
    """Test reward calculations across multiple rounds."""
    p = Participant()
    
    # Add participant to multiple rounds with different rewards
    rounds_data = [
        (generate_ethereum_address(), Role.VALIDATOR, 100),
        (generate_ethereum_address(), Role.LEADER, 200),
        (generate_ethereum_address(), Role.APPEALANT, -50)  # Penalty
    ]
    
    # Add rounds and set rewards
    for round_id, role, reward in rounds_data:
        p.add_to_round(round_id, role)
        p.rounds[round_id].reward = reward
    
    # Test total rewards calculation
    expected_total = sum(reward for _, _, reward in rounds_data)
    assert p.get_total_rewards() == expected_total


def test_string_representation():
    """Test the string representation of a participant."""
    p = Participant(id="0x123")
    
    # Add some rounds and rewards
    round_id = generate_ethereum_address()
    p.add_to_round(round_id, Role.VALIDATOR)
    p.rounds[round_id].reward = 100
    
    # Test string representation
    repr_str = str(p)
    assert "Participant" in repr_str
    assert "id=0x123" in repr_str
    assert "rounds=1" in repr_str
    assert "total_rewards=100" in repr_str


def test_round_data_immutability():
    """Test that RoundData objects maintain their integrity."""
    round_id = generate_ethereum_address()
    round_data = RoundData(round_id, Role.VALIDATOR, 0)
    
    # Verify RoundData attributes
    assert round_data.id == round_id
    assert round_data.role == Role.VALIDATOR
    assert round_data.reward == 0
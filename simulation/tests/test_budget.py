import pytest
from unittest.mock import patch

from simulation.models.budget import Budget
from simulation.models.enums import RoundType, AppealType
from simulation.errors import OutOfGasError
from simulation.utils import generate_ethereum_address, generate_validators_per_round_sequence

@pytest.fixture(autouse=True)
def mock_validator_sequence():
    """Mock the validator sequence to return a fixed length for testing."""
    with patch(
        "simulation.models.budget.generate_validators_per_round_sequence"
    ) as mock:
        # Create sequence starting from MIN_NUM_VALS doubling each time
        sequence = [5, 11, 23, 47, 95, 191, 383, 767, 1000]  # Based on MIN_NUM_VALS=5, MAX_NUM_VALS=1000
        mock.return_value = sequence
        yield mock


@pytest.fixture
def simple_budget():
    """Basic budget setup for testing."""
    sequence = generate_validators_per_round_sequence()
    return Budget(
        leader_time_units=50,
        validator_time_units=30,
        rotations_per_round=[20 for _ in range(len(sequence))],
        appeal_rounds=5,
        total_internal_messages_budget=500,
        external_messages_budget=100
    )


def test_budget_initialization(simple_budget):
    """Test basic budget initialization and total gas calculation."""
    # Calculate expected initial round budget (leader + validators for first round)
    sequence = generate_validators_per_round_sequence()
    initial_round_budget = simple_budget.leader_time_units + simple_budget.validator_time_units * sequence[0]

    assert simple_budget.initial_round_budget == initial_round_budget


def test_invalid_budget_initialization():
    """Test validation of budget initialization with incorrect rotation budget length."""
    sequence = generate_validators_per_round_sequence()
    with pytest.raises(ValueError):
        Budget(
            leader_time_units=50,
            validator_time_units=30,
            rotations_per_round=[20, 20],  # Wrong length
            appeal_rounds=5,
            total_internal_messages_budget=500,
        )


def test_spend_initial_round_budget(simple_budget):
    """Test spending budget for initial round."""
    round_id = generate_ethereum_address()
    initial_budget = simple_budget.initial_round_budget
    
    simple_budget.spend_round_budget(round_id, RoundType.INITIAL, 0)
    
    assert simple_budget.initial_round_budget < initial_budget


def test_spend_rotation_round_budget(simple_budget):
    """Test spending budget for rotation round."""
    round_id = generate_ethereum_address()
    initial_rotation_budget = simple_budget.rotation_budget
    
    simple_budget.spend_round_budget(round_id, RoundType.ROTATE, 1)  # 1 for second round
    
    assert simple_budget.rotation_budget < initial_rotation_budget


def test_spend_appeal_round_budget(simple_budget):
    """Test spending budget for different types of appeal rounds."""
    round_id = generate_ethereum_address()
    initial_appeal_budget = simple_budget.appeal_rounds_budget
    
    # Test leader appeal
    simple_budget.spend_round_budget(round_id, AppealType.LEADER, 1)
    assert simple_budget.appeal_rounds_budget < initial_appeal_budget
    
    # Test validator appeal
    current_appeal_budget = simple_budget.appeal_rounds_budget
    simple_budget.spend_round_budget(round_id, AppealType.VALIDATOR, 1)
    assert simple_budget.appeal_rounds_budget < current_appeal_budget
    
    # Test tribunal appeal
    current_appeal_budget = simple_budget.appeal_rounds_budget
    simple_budget.spend_round_budget(round_id, AppealType.TRIBUNAL, 1)
    assert simple_budget.appeal_rounds_budget < current_appeal_budget


def test_out_of_gas_handling(simple_budget):
    """Test handling of out-of-gas situations."""
    round_id = generate_ethereum_address()
    
    # Deplete initial round budget
    simple_budget.initial_round_budget = 0
    
    with pytest.raises(OutOfGasError):
        simple_budget.spend_round_budget(round_id, RoundType.INITIAL, 0)

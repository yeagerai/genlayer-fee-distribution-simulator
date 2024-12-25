import pytest
from unittest.mock import patch
from simulation.models.transaction import Transaction
from simulation.models.budget import Budget
from simulation.models.enums import LeaderResult, Vote
from simulation.utils import generate_ethereum_address
from simulation.models.participant import Participant
from simulation.utils import generate_validators_per_round_sequence

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


def test_initial_round():
    """Test starting a transaction with initial round."""
    # Create validator pool
    initial_validators_pool = {
        generate_ethereum_address(): Participant() for _ in range(1000)
    }

    # Get sequence length for budget initialization
    sequence = generate_validators_per_round_sequence()
    
    # Create budget with correct sequence length
    budget = Budget(
        leader_time_units=50,
        validator_time_units=30,
        rotations_per_round=[20 for _ in range(len(sequence))],
        appeal_rounds=5,
        total_internal_messages_budget=1000,
    )

    # Create transaction
    tx = Transaction(budget, initial_validators_pool)

    # Get required number of validators for first round
    num_validators = sequence[0]  # Use first number from sequence
    
    # Start first round
    tx.start(
        leader_result=LeaderResult.RECEIPT,
        voting_vector=[Vote.AGREE] * num_validators  # Use correct number of validators
    )

    # Print rewards
    tx.print_current_rewards()

def test_rotation_round():
    """Test rotation round after initial round."""
    # Create validator pool
    initial_validators_pool = {
        generate_ethereum_address(): Participant() for _ in range(1000)
    }

    sequence = generate_validators_per_round_sequence()
    
    budget = Budget(
        leader_time_units=50,
        validator_time_units=30,
        rotations_per_round=[20 for _ in range(len(sequence))],
        appeal_rounds=5,
        total_internal_messages_budget=1000,
    )

    tx = Transaction(budget, initial_validators_pool)

    # Start with initial round
    tx.start(
        leader_result=LeaderResult.RECEIPT,
        voting_vector=[Vote.DISAGREE] * sequence[0]
    )

    # Add rotation round
    tx.rotate(
        leader_result=LeaderResult.RECEIPT,
        voting_vector=[Vote.AGREE] * sequence[1]  # Use second number from sequence
    )

    # Verify we have two rounds
    assert len(tx.rounds) == 2
    
    # Verify the second round is properly linked to the first
    assert tx.rounds[1].previous_round_id == tx.rounds[0].id

    # Print rewards to verify distribution
    tx.print_current_rewards()
import pytest
from unittest.mock import patch

from simulation.models.transaction_budget import (
    TransactionBudget,
    PresetLeaf,
    PresetBranch,
)
from simulation.errors import OutOfGasError


# Mock the sequence generation to always return a fixed length for tests
@pytest.fixture(autouse=True)
def mock_validator_sequence():
    """Mock the validator sequence to return a fixed length for testing."""
    with patch(
        "simulation.models.transaction_budget.generate_validators_per_round_sequence"
    ) as mock:
        mock.return_value = [3, 7, 15]  # Fixed sequence for testing
        yield mock


def test_total_gas_calculation():
    budget = TransactionBudget(
        initial_leader_budget=100,
        initial_validator_budget=200,
        rotation_budget=[50, 50, 50],
        appeal_rounds_budget=225,  # Total gas for appeal rounds
        total_internal_messages_budget=500,
        external_messages_budget_guess=[25, 25],
    )

    expected_total = (
        100  # initial_leader_budget
        + 200  # initial_validator_budget
        + 150  # sum of rotation_budget
        + 225  # appeal_rounds_budget
        + 500  # total_internal_messages_budget
        + 50  # sum of external_messages_budget_guess
    )

    assert budget.total_gas == expected_total
    assert budget.remaining_gas == expected_total

    # Test gas usage tracking
    used, remaining, percentage = budget.get_gas_usage()
    assert used == 0
    assert remaining == expected_total
    assert percentage == 0.0

    # Test after some gas usage
    gas_to_use = 100
    budget.remaining_gas -= gas_to_use
    used, remaining, percentage = budget.get_gas_usage()
    assert used == gas_to_use
    assert remaining == expected_total - gas_to_use
    assert percentage == (gas_to_use / expected_total) * 100


@pytest.fixture
def simple_budget():
    """Basic budget setup for testing."""
    return TransactionBudget(
        initial_leader_budget=100,
        initial_validator_budget=200,
        rotation_budget=[50, 50, 50],
        appeal_rounds_budget=225,  # Total gas for appeal rounds
        total_internal_messages_budget=500,
        external_messages_budget_guess=[25, 25],
    )


@pytest.fixture
def preset_budget():
    """Budget with preset patterns for testing."""
    leaf1 = PresetLeaf(
        initial_leader_budget=50,
        initial_validator_budget=100,
        rotation_budget=[20, 20, 20],  # Changed to length 3
        appeal_rounds_budget=60,
    )

    leaf2 = PresetLeaf(
        initial_leader_budget=30,
        initial_validator_budget=60,
        rotation_budget=[10, 10, 10],  # Changed to length 3
        appeal_rounds_budget=30,
    )

    branch = PresetBranch(
        initial_leader_budget=100,
        initial_validator_budget=200,
        rotation_budget=[40, 40, 40],  # Changed to length 3
        appeal_rounds_budget=120,
        internal_messages_budget_guess={"msg1": "leaf1", "msg2": "leaf2"},
        external_messages_budget_guess=[50, 50],
    )

    return TransactionBudget(
        initial_leader_budget=100,
        initial_validator_budget=200,
        rotation_budget=[50, 50, 50],  # Changed to length 3
        appeal_rounds_budget=150,
        preset_leafs={"leaf1": leaf1, "leaf2": leaf2},
        preset_branches={"branch1": branch},
        total_internal_messages_budget=1000,
        external_messages_budget_guess=[100],
    )


def test_budget_initialization(simple_budget):
    """Test basic budget initialization and total gas calculation."""
    expected_total = 100 + 200 + 150 + 225 + 500 + 50  # All budgets summed
    assert simple_budget.total_gas == expected_total
    assert simple_budget.remaining_gas == expected_total
    assert not simple_budget.failed


def test_gas_usage_tracking(simple_budget):
    """Test gas usage calculation and tracking."""
    initial_gas = simple_budget.remaining_gas
    gas_to_use = 100

    simple_budget.remaining_gas -= gas_to_use
    used, remaining, percentage = simple_budget.get_gas_usage()

    assert used == gas_to_use
    assert remaining == initial_gas - gas_to_use
    assert percentage == (gas_to_use / initial_gas) * 100


def test_preset_leaf_computation(preset_budget):
    """Test gas computation for leaf presets."""
    gas = preset_budget.compute_internal_message_budget("leaf1")
    expected = (
        50  # initial_leader_budget
        + 100  # initial_validator_budget
        + 60  # sum of rotation_budget (20 * 3)
        + 60  # appeal_rounds_budget
    )
    assert gas == expected


def test_preset_branch_computation(preset_budget):
    """Test gas computation for branch presets with references."""
    gas = preset_budget.compute_internal_message_budget("branch1")

    # Branch own gas + referenced leaf presets
    leaf1_gas = 50 + 100 + 60 + 60  # leaf1's total gas
    leaf2_gas = 30 + 60 + 30 + 30  # leaf2's total gas
    branch_own_gas = (
        100  # initial_leader_budget
        + 200  # initial_validator_budget
        + 120  # sum of rotation_budget (40 * 3)
        + 120  # appeal_rounds_budget
        + 100  # sum of external_messages_budget_guess
    )

    expected = branch_own_gas + leaf1_gas + leaf2_gas
    assert gas == expected


def test_out_of_gas_handling(preset_budget):
    """Test handling of out-of-gas situations."""
    # Use up most of the gas
    preset_budget.remaining_gas = 100

    with pytest.raises(OutOfGasError):
        preset_budget.compute_internal_message_budget("branch1")

    assert preset_budget.failed


def test_round_budget_access(simple_budget):
    """Test access to round-specific budgets."""
    rotation, appeal = simple_budget.get_round_budgets(1)
    assert rotation == 50
    assert appeal == 225

    with pytest.raises(ValueError):
        simple_budget.get_round_budgets(5)  # Exceeds available rounds


def test_invalid_budget_initialization():
    """Test validation of budget initialization."""
    with pytest.raises(ValueError):
        TransactionBudget(
            initial_leader_budget=100,
            initial_validator_budget=200,
            rotation_budget=[50, 50],
            appeal_rounds_budget=75,
            total_internal_messages_budget=500,
        )

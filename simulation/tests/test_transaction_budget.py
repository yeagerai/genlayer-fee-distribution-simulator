import pytest

from simulation.models.transaction_budget import (
    TransactionBudget,
    PresetLeaf,
    PresetBranch,
)
from simulation.errors import OutOfGasError


def test_total_gas_calculation():
    budget = TransactionBudget(
        initial_leader_budget=100,
        initial_validator_budget=200,
        rotation_budget=[50, 50, 50],
        appeal_rounds_budget=[75, 75, 75],
        total_internal_messages_budget=500,
        external_messages_budget_guess=[25, 25],
    )

    expected_total = (
        100  # initial_leader_budget
        + 200  # initial_validator_budget
        + 150  # sum of rotation_budget
        + 225  # sum of appeal_rounds_budget
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
        appeal_rounds_budget=[75, 75, 75],
        total_internal_messages_budget=500,
        external_messages_budget_guess=[25, 25],
    )


@pytest.fixture
def preset_budget():
    """Budget with preset patterns for testing."""
    leaf1 = PresetLeaf(
        initial_leader_budget=50,
        initial_validator_budget=100,
        rotation_budget=[20, 20],
        appeal_rounds_budget=[30, 30],
    )

    leaf2 = PresetLeaf(
        initial_leader_budget=30,
        initial_validator_budget=60,
        rotation_budget=[10, 10],
        appeal_rounds_budget=[15, 15],
    )

    branch = PresetBranch(
        initial_leader_budget=100,
        initial_validator_budget=200,
        rotation_budget=[40, 40],
        appeal_rounds_budget=[60, 60],
        internal_messages_budget_guess={"msg1": "leaf1", "msg2": "leaf2"},
        external_messages_budget_guess=[50, 50],
    )

    return TransactionBudget(
        initial_leader_budget=100,
        initial_validator_budget=200,
        rotation_budget=[50, 50],
        appeal_rounds_budget=[75, 75],
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
    expected = 50 + 100 + 40 + 60  # Sum of leaf1's budgets
    assert gas == expected


def test_preset_branch_computation(preset_budget):
    """Test gas computation for branch presets with references."""
    gas = preset_budget.compute_internal_message_budget("branch1")

    # Branch own gas + referenced leaf presets
    leaf1_gas = 50 + 100 + 40 + 60
    leaf2_gas = 30 + 60 + 20 + 30
    branch_own_gas = 100 + 200 + 80 + 120 + 100  # Including external messages

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
    assert appeal == 75

    with pytest.raises(ValueError):
        simple_budget.get_round_budgets(5)  # Exceeds available rounds


def test_invalid_budget_initialization():
    """Test validation of budget initialization."""
    with pytest.raises(ValueError):
        TransactionBudget(
            initial_leader_budget=100,
            initial_validator_budget=200,
            rotation_budget=[50, 50],  # Different length
            appeal_rounds_budget=[75, 75, 75],
            total_internal_messages_budget=500,
        )

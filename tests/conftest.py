import pytest
from fee_simulator.models.custom_types import TransactionBudget
from fee_simulator.models.constants import addresses_pool


def pytest_addoption(parser):
    parser.addoption(
        "--verbose-output",
        action="store_true",
        default=False,
        help="Enable verbose output for tests (e.g., print fee distributions)",
    )


@pytest.fixture
def verbose(request):
    """Fixture to determine if verbose output is enabled."""
    return request.config.getoption("--verbose-output")


@pytest.fixture
def default_budget():
    """Fixture for a default transaction budget."""
    return TransactionBudget(
        leaderTimeout=100,
        validatorsTimeout=200,
        appealRounds=1,
        rotations=[1],
        senderAddress=addresses_pool[10],
        appeals=[],
        staking_distribution="constant",
    )

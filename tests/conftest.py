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

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--verbose-output",
        action="store_true",
        default=False,
        help="Enable verbose output for tests (e.g., print fee distributions)",
    )
    parser.addoption(
        "--debug-output",
        action="store_true",
        default=False,
        help="Enable debug output for tests (e.g., print fee distributions)",
    )


@pytest.fixture
def verbose(request):
    """Fixture to determine if verbose output is enabled."""
    return request.config.getoption("--verbose-output")


@pytest.fixture
def debug(request):
    """Fixture to determine if debug output is enabled."""
    return request.config.getoption("--debug-output")

import re
import pytest
import numpy as np
from simulation.utils import (
    generate_ethereum_address,
    generate_validators_per_round_sequence,
    set_random_seed,
)
from simulation.config_constants import MAX_NUM_VALS, MIN_NUM_VALS


def test_generate_ethereum_address():
    """Test Ethereum address generation."""
    address = generate_ethereum_address()

    # Check format
    assert address.startswith("0x")
    assert len(address) == 42
    assert re.match(r"^0x[0-9a-f]{40}$", address)

    # Check uniqueness
    addresses = [generate_ethereum_address() for _ in range(100)]
    assert len(set(addresses)) == 100


def test_generate_validators_per_round_sequence():
    """Test validator sequence generation."""
    sequence = generate_validators_per_round_sequence()

    # Check sequence properties
    assert sequence[0] == MIN_NUM_VALS
    assert sequence[-1] == MAX_NUM_VALS
    assert all(x <= MAX_NUM_VALS for x in sequence)
    assert all(x >= MIN_NUM_VALS for x in sequence)

    # Check sequence follows 2n + 1 pattern
    for i in range(len(sequence) - 1):
        if sequence[i + 1] != MAX_NUM_VALS:
            assert sequence[i + 1] == 2 * sequence[i] + 1

    # Check sequence is strictly increasing
    assert all(sequence[i] < sequence[i + 1] for i in range(len(sequence) - 1))


def test_set_random_seed():
    """Test random seed setting for reproducibility."""
    # Test with a specific seed
    seed = 42
    set_random_seed(seed)

    # Generate some random ethereum addresses
    random_sequence1 = [generate_ethereum_address() for _ in range(5)]

    # Reset seed and generate again
    set_random_seed(seed)
    random_sequence2 = [generate_ethereum_address() for _ in range(5)]

    # Check sequences match
    assert random_sequence1 == random_sequence2
    
    # Generate different sequence with different seed
    set_random_seed(43)
    random_sequence3 = [generate_ethereum_address() for _ in range(5)]
    assert random_sequence1 != random_sequence3  # Verify sequences are different with different seeds


def test_validator_sequence_edge_cases():
    """Test validator sequence generation with different MIN/MAX values."""
    # Test when MIN_NUM_VALS is close to MAX_NUM_VALS
    if MIN_NUM_VALS > MAX_NUM_VALS // 2:
        sequence = generate_validators_per_round_sequence()
        assert len(sequence) == 2  # Should only have MIN_NUM_VALS and MAX_NUM_VALS

    # Test sequence never exceeds MAX_NUM_VALS
    sequence = generate_validators_per_round_sequence()
    assert all(x <= MAX_NUM_VALS for x in sequence)

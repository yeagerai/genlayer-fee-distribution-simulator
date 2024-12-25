# Optimistic Democracy Consensus Simulator

A simulation framework for testing and analyzing the Optimistic Democracy consensus mechanism. The project provides tools for simulating transaction processing, reward distribution, and appeal mechanisms.

## Core Concepts

The simulator models several key components of the Optimistic Democracy system:

1. **Transactions**
   - Managed through rounds of consensus
   - Support for initial, rotation, and appeal rounds
   - Automatic state progression based on voting outcomes

2. **Participants**
   - Dynamic role assignment (leader, validator)
   - Reward tracking per round
   - Support for multiple rounds participation

3. **Reward System**
   - Time-unit based rewards and penalties
   - Budget management per transaction
   - Role-specific reward distribution

4. **Appeal Mechanism**
   - Support for leader, validator, and tribunal appeals
   - Bond-based appeal system
   - Success calculation based on voting outcomes

## Project Structure

```
simulation/
├── models/
│   ├── budget.py           # Transaction budget management
│   ├── enums.py           # System enumerations
│   ├── participant.py      # Participant state and behavior
│   ├── reward_manager.py   # Reward distribution logic
│   ├── round.py           # Round types and management
│   └── transaction.py      # Transaction orchestration
├── tests/
│   ├── test_budget.py
│   ├── test_participant.py
│   ├── test_round.py
│   └── test_transaction.py
├── utils.py               # Helper functions
└── config_constants.py    # System configuration
```

## Key Features

- **Dynamic Validator Selection**: Automatically scales validator count between rounds
- **Flexible Round Management**: Supports multiple round types with different voting mechanisms
- **Comprehensive Reward System**: Tracks and distributes rewards based on participant behavior
- **Automated State Transitions**: Determines next steps based on voting outcomes
- **Test Coverage**: Extensive test suite for all components

## Testing

Run the test suite using pytest:

```bash
pytest
```

To run it with prints:

```bash
pytest -s
```

## Contributing

Contributions are welcome! Please ensure tests pass and add new tests for new functionality.
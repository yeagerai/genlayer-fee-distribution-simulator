# Optimistic Democracy Consensus Simulator

A simulation framework for Optimistic Democracy consensus mechanism. The project includes both a backend simulation engine and a Streamlit-based frontend interface.

## Features

The simulator provides four main interfaces through its Streamlit frontend:

1. **Manual Transaction Runner**
   - Execute individual transactions
   - Step through consensus rounds
   - Visualize participant interactions
   - Track gas usage in real-time

2. **Statistical Simulator**
   - Run multiple transactions with varying parameters
   - Generate performance metrics
   - Analyze success rates and gas usage patterns
   - Export simulation results

3. **Configuration Manager**
   - Adjust system parameters
   - Set validator counts and thresholds
   - Configure gas limits and preset patterns

4. **Test Suite Runner**
   - Execute predefined test scenarios
   - Test edge cases and failure modes
   - Validate consensus mechanism
   - Generate comprehensive reports

## Architecture

The simulator backend is organized into several key components:

```
simulation/
├── init.py
├── config_constants.py # System-wide constants
├── errors.py # Custom exceptions
├── utils.py # Utility functions
├── models/
│ ├── init.py
│ ├── enums.py # System enums (Role, Vote, etc.)
│ ├── participant.py # Participant model
│ ├── appeal.py # Appeal mechanism
│ ├── round.py # Round management
│ └── transaction_budget.py # Gas budget management
└── tests/
├── init.py
├── test_participant.py
├── test_appeal.py
├── test_round.py
└── test_transaction_budget.py
```


### Core Components

- **Participant**: Represents actors in the system with different roles (leader, validator, appealant)
- **Appeal**: Manages the appeal process with different types and voting mechanisms
- **Round**: Handles consensus rounds with validator rotation and voting
- **TransactionBudget**: Manages gas costs through preset patterns and budget tracking
- **OptTransaction**: Represents a transaction in the system, including its gas cost and budget allocation

## Testing

The project uses pytest for testing. To run all tests:

```
pytest
```

To run a specific test:

```
pytest tests/test_participant.py
```


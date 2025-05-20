# GenLayer Fee Distribution Simulator

## Overview

The GenLayer Fee Distribution Simulator is a Python-based tool designed to model and analyze the fee distribution mechanics of a blockchain validator network, specifically for the GenLayer protocol. It simulates how transaction fees are allocated among participants (leaders, validators, senders, and appealants) based on their roles, voting behavior, and consensus outcomes. The simulator supports a variety of scenarios, including normal rounds, leader and validator appeals, timeouts, and penalties for non-compliance, providing insights into the economic incentives of the network.

## Key Features

- **Role-Based Fee Distribution**: Allocates fees to participants based on their roles (Leader, Validator, Sender, Appealant).
- **Consensus-Driven Rewards and Penalties**: Rewards majority voters and penalizes minority or idle participants.
- **Appeal Mechanisms**: Simulates successful and unsuccessful appeals with appeal bond calculations.
- **Comprehensive Testing Suite**: Includes unit tests, scenario-based tests, and edge-case validation.
- **Visualization Tools**: Provides formatted tables for transaction results, fee distributions, and summary statistics.
- **Modular Design**: Organized into core logic, display utilities, and testing modules for easy extension.

## Project Structure

The project is organized into the following key directories and files:

- **fee_simulator/**
    - **core/**: Core logic for fee distribution and transaction processing.
        - `round_fee_distribution/*.py`: Implements fee distribution rules for various round types (e.g., normal rounds, appeals, timeouts).
        - `bond_computing.py`: Calculates appeal bonds based on round indices and timeouts.
        - `burns.py`: Computes burn amounts for unsuccessful appeals.
        - `deterministic_violation.py`: Handles slashing for hash mismatches.
        - `idleness.py`: Manages idle validator slashing and reserve replacements.
        - `majority.py`: Determines vote and hash majorities.
        - `refunds.py`: Calculates sender refunds.
        - `round_labeling.py`: Labels rounds based on voting patterns and context.
        - `transaction_processing.py`: Orchestrates the fee distribution process.
    - **display/**: Visualization utilities for formatted output.
        - `fee_distribution.py`: Displays detailed fee event tables.
        - `summary_table.py`: Shows summarized fee distributions and round labels.
        - `transaction_results.py`: Visualizes round and rotation details.
        - `utils.py`: Formatting helpers for colored output and table creation.
    - **fee_aggregators/**: Aggregates financial metrics per address.
        - `address_metrics.py`: Computes costs, earnings, burns, and stakes.
    - `constants.py`: Defines constants like round sizes and penalty coefficients.
    - `models.py`: Pydantic models for data validation (e.g., FeeEvent, TransactionBudget).
    - `types.py`: Type definitions for votes, roles, and round labels.
    - `utils.py`: Utility functions for address generation and stake initialization.
- **tests/**: Comprehensive test suite.
    - `budget_and_refunds/*.py`: Tests for budget calculations and refunds.
    - `round_types_tests/*.py`: Scenario-based tests for various round types.
    - `slashing/*.py`: Tests for slashing mechanisms (e.g., idleness, violations).
    - `conftest.py`: Pytest configuration for verbose/debug output.
- `requirements.txt`: Lists project dependencies.

## How It Works

### Core Components

1. **Rounds and Rotations**:
    
    - A transaction consists of one or more rounds, each containing rotations.
    - Rotations hold votes from validators and leaders, influencing fee distribution.
2. **Vote Types**:
    
    - `AGREE`, `DISAGREE`, `TIMEOUT`, `IDLE`: Validator votes.
    - `LEADER_RECEIPT`, `LEADER_TIMEOUT`: Leader-specific actions.
    - Votes may include hashes for validation.
3. **Round Types**:
    
    - `NORMAL_ROUND`: Standard validation round.
    - `APPEAL_LEADER_SUCCESSFUL/UNSUCCESSFUL`: Leader appeal outcomes.
    - `APPEAL_VALIDATOR_SUCCESSFUL/UNSUCCESSFUL`: Validator appeal outcomes.
    - `LEADER_TIMEOUT_50_PERCENT`, `LEADER_TIMEOUT_150_PREVIOUS_NORMAL_ROUND`, etc.: Timeout scenarios.
    - `SPLIT_PREVIOUS_APPEAL_BOND`: Distributes prior appeal bonds.
4. **Fee Distribution Process**:
    
    - **Initialization**: Stakes are assigned to participants.
    - **Idle Handling**: Idle validators are slashed and replaced by reserves.
    - **Violation Handling**: Validators with mismatched hashes are slashed.
    - **Round Labeling**: Rounds are labeled based on votes and context.
    - **Fee Allocation**: Fees are distributed per round label, rewarding majority voters and penalizing others.
    - **Refunds**: Senders receive refunds for overpaid fees.

### Example Workflow

1. A transaction is defined with a `TransactionBudget` (leader/validator timeouts, sender, appeals) and `TransactionRoundResults` (rounds and votes).
2. The `process_transaction` function:
    - Initializes stakes.
    - Subtracts the total cost from the sender.
    - Handles idle validators and violations.
    - Labels rounds and distributes fees.
    - Computes and applies sender refunds.
3. Results are visualized using `display_summary_table`, `display_fee_distribution`, and `display_transaction_results`.

## Installation

1. Clone the repository:
    
    ```bash
    git clone <repository_url>
    cd genlayer-fee-simulator
    ```
    
2. Create a virtual environment and activate it:
    
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
    
3. Install dependencies:
    
    ```bash
    pip install -r requirements.txt
    ```
    

## Usage

### Running Tests

To run the entire test suite:

```bash
pytest
```

To run the entire test suite and log all the results in a file for future analysis:

```
pytest -s --verbose-output --debug-output > tests.txt 
```

And then `cat tests.txt` to visualize it.

To run a specific test with verbose and debug output (displays formatted tables):

```bash
pytest tests/round_types_tests/test_normal_round.py -s --verbose-output --debug-output
```

### Creating Custom Scenarios

You can create and simulate custom transaction scenarios programmatically:

```python
from fee_simulator.models import TransactionBudget, TransactionRoundResults, Round, Rotation, FeeEvent
from fee_simulator.core.transaction_processing import process_transaction
from fee_simulator.utils import generate_random_eth_address
from fee_simulator.display import display_summary_table, display_transaction_results, display_fee_distribution

# Generate addresses
addresses = [generate_random_eth_address() for _ in range(6)]

# Define budget
budget = TransactionBudget(
    leaderTimeout=100,
    validatorsTimeout=200,
    appealRounds=0,
    rotations=[0],
    senderAddress=addresses[5],
    appeals=[],
    staking_distribution="constant"
)

# Define transaction results
rotation = Rotation(
    votes={
        addresses[0]: ["LEADER_RECEIPT", "AGREE"],
        addresses[1]: "AGREE",
        addresses[2]: "AGREE",
        addresses[3]: "AGREE",
        addresses[4]: "DISAGREE"
    }
)
results = TransactionRoundResults(rounds=[Round(rotations=[rotation])])

# Process transaction
fee_events, round_labels = process_transaction(addresses, results, budget)

# Display results
display_summary_table(fee_events, results, budget, round_labels)
display_transaction_results(results, round_labels)
display_fee_distribution(fee_events)
```

## Testing Framework

The test suite covers:

- **Unit Tests**: Validate individual components (e.g., budget calculations, refunds).
- **Scenario-Based Tests**: Test specific round types (e.g., `test_normal_round.py`, `test_appeal_leader_successful.py`).
- **Slashing Tests**: Verify slashing for idleness and deterministic violations.
- **Edge Cases**: Handle scenarios like empty rounds, undetermined majorities, and unsuccessful appeals.

Run tests with verbose output to inspect detailed fee distributions and transaction outcomes.

## Use Cases

- **Economic Analysis**: Evaluate the incentive structure of the GenLayer protocol.
- **Protocol Validation**: Simulate fee distribution before deploying protocol changes.
- **Education**: Understand blockchain consensus and fee mechanics.
- **Development**: Test and refine fee distribution algorithms.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

# GenLayer Fee Distribution Simulator

## Overview

This project implements a comprehensive fee distribution system for blockchain validator networks. It models how transaction fees are distributed among network participants based on their roles, voting behavior, and consensus patterns. The system supports complex scenarios including normal validation rounds, appeals, timeouts, and various consensus patterns.

## Key Features

- **Role-based Fee Distribution:** Allocates fees to different roles including leaders, validators, senders, and appealants

- **Consensus-Based Rewards:** Rewards validators who vote with the majority and penalizes those in the minority

- **Appeal Processing:** Handles appeal bonds, successful and unsuccessful appeals

- **Comprehensive Testing:** Includes statistical and combinatorial testing frameworks

- **Visualization:** Pretty-prints transaction results and fee distributions

## Project Structure

- `distribute_fees.py`: Core fee distribution logic

- `majority.py`: Functions for determining vote majority

- `custom_types.py`: Pydantic models defining the system's data structures

- `constants.py`: Configuration constants

- `utils.py`: Utility functions for formatting and generating test data

- `fee_distribution_tests.py`: Specific test scenarios

- `statistical_testing.py`: Statistical sampling-based tests

- `combinatorial_testing.py`: Comprehensive combinatorial testing

## How It Works

### Core Components

1. Rounds & Rotations:

- A transaction includes one or more rounds

- Each round contains one or more rotations

- Each rotation contains votes from validators

2. Vote Types:

- Agree: Validator agrees with the transaction

- Disagree: Validator disagrees with the transaction

- Timeout: Validator timed out without casting a vote

- LeaderReceipt: Special vote type for the round leader

3. Round Types:

- normal_round: Standard validation round

- appeal_round: Round initiated by an appeal

- Various other specialized round types for different scenarios

4. Fee Distribution Logic:

- Leaders receive timeout fees for leadership responsibilities

- Validators in the majority receive validation fees

- Validators in the minority receive penalties (negative fees)

- Appealants receive or lose appeal bonds based on appeal success

- Senders may receive portions of unsuccessful appeal bonds

### Fee Distribution Process

1. Rounds are labeled based on their context and voting patterns

2. Each round's fees are distributed according to its label

3. Fees accumulate in a FeeDistribution object mapping addresses to their roles and fee amounts

4. The final distribution shows how much each participant earned or lost

## Testing Framework

The project includes three types of testing:

1. Scenario-based Testing (fee_distribution_tests.py):

- Predefined scenarios testing specific edge cases

- Clear visualization of inputs and outputs

2. Statistical Testing (statistical_testing.py):

- Uses prior probabilities to generate realistic scenarios

- Models typical network behavior

- Tests fee distribution across likely scenarios

3. Combinatorial Testing (combinatorial_testing.py):

- Systematically tests all combinations of factors

- Provides comprehensive coverage of possible states

- Includes complexity analysis to understand testing boundaries

## Use Cases

This system is useful for:

- Economic Analysis: Studying incentive structures in GenLayer Protocol

- Protocol Simulation: Validating economic models before deployment

## Getting Started

1. Run predefined test scenarios:
    
```bash
   python fee_distribution_tests.py
``` 

2. Run statistical tests:
    
```bash    
   python statistical_testing.py
```    

2. Run combinatorial tests:
```    
   python combinatorial_testing.py
``` 

2. Create and run custom scenarios:
    
```python
       from custom_types import (
    
           FeeDistribution, TransactionBudget, 
    
           TransactionRoundResults, Round, Rotation
    
       )
    
       from distribute_fees import distribute_fees
    
       # Initialize fee distribution
    
       fee_distribution = initialize_fee_distribution()
    
       # Create your custom scenario
    
       transaction_results = TransactionRoundResults(...)
    
       transaction_budget = TransactionBudget(...)
    
       # Distribute fees
    
       result, round_labels = distribute_fees(
    
           fee_distribution=fee_distribution,
    
           transaction_results=transaction_results,
    
           transaction_budget=transaction_budget
    
       )
```    

## Visualization

The system includes robust visualization for:

- Transaction structure with color-coded vote types

- Round labels and consensus outcomes

- Detailed fee distribution with color-coded positive/negative amounts

- Summary statistics for overall fee distribution

## Future Development

- Auto-computing of bonds per unsuccessful appeal type

- Building a frontend with Streamlit for easy to see

- Adding more unit tests

- Expanding documentation

## Running tests

To run a specific test, looking at the print statements (fancy tables) in the test file:

```bash
pytest tests/folder/test_file.py -s --verbose-output --debug-output
```

To run all tests, use the following command:

```bash
pytest 
```

## Summary

This GenLayer fee distribution simulator provides a sophisticated model for incentivizing correct behavior in validator networks. By rewarding consensus and penalizing deviation, it creates economic incentives for network health while providing mechanisms for appeals and error correction.

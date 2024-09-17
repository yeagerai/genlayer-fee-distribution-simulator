# app.py

import streamlit as st
import numpy as np
import altair as alt
from simulation.models import Validator, Investor
from simulation.simulation import (
    initialize_validators,
    initialize_investors,
    initial_delegation,
    simulate_transactions,
)
from simulation.utils import prepare_validator_data, prepare_investor_data

# Set the page configuration
st.set_page_config(page_title="Validator Simulation", layout="wide")

# Title and description
st.title("Validator and Investor Stake Simulation")

st.markdown(
    """
This simulation models a network of validators and investors in a staking system.
Validators process transactions and receive rewards, while investors delegate their stakes
to validators to earn a share of the rewards. Use the controls in the sidebar to adjust
the simulation parameters and observe how the stakes evolve over time.
"""
)

# Sidebar parameters
st.sidebar.header("Simulation Parameters")

N_validators = st.sidebar.slider(
    "Number of Validators", min_value=5, max_value=50, value=10
)
N_investors = st.sidebar.slider(
    "Number of Investors", min_value=10, max_value=200, value=50
)
min_stake_validator = st.sidebar.number_input(
    "Minimum Validator Stake", min_value=1, value=50
)
max_stake_validator = st.sidebar.number_input(
    "Maximum Validator Stake", min_value=1, value=100
)
min_stake_investor = st.sidebar.number_input(
    "Minimum Investor Stake", min_value=1, value=10
)
max_stake_investor = st.sidebar.number_input(
    "Maximum Investor Stake", min_value=1, value=50
)
num_transactions = st.sidebar.slider(
    "Number of Transactions", min_value=10, max_value=500, value=100
)
reward = st.sidebar.number_input("Reward per Transaction", min_value=1, value=50)
selection_method = st.sidebar.selectbox(
    "Selection Method", options=["proportional", "logarithmic"], index=0
)

# Run the simulation
validators = initialize_validators(
    N_validators, min_stake_validator, max_stake_validator
)
investors = initialize_investors(N_investors, min_stake_investor, max_stake_investor)
initial_delegation(investors, validators)
simulate_transactions(
    validators, investors, num_transactions, reward, method=selection_method
)

# Prepare data for plotting
validator_df = prepare_validator_data(validators)
investor_df = prepare_investor_data(investors)

# Plotting with Altair
st.header("Simulation Results")

st.subheader("Validators Stake Evolution")
validator_chart = (
    alt.Chart(validator_df)
    .mark_line()
    .encode(
        x="Transaction",
        y="Stake",
        color="Validator",
        tooltip=["Validator", "Transaction", "Stake"],
    )
    .interactive()
)
st.altair_chart(validator_chart, use_container_width=True)

st.subheader("Investors Stake Evolution")
investor_chart = (
    alt.Chart(investor_df)
    .mark_line()
    .encode(
        x="Transaction",
        y="Stake",
        color="Investor",
        tooltip=["Investor", "Transaction", "Stake"],
    )
    .interactive()
)
st.altair_chart(investor_chart, use_container_width=True)

# Additional explanation
st.markdown(
    """
### How the Simulation Works

- **Validators**: Entities that process transactions and receive rewards. Each validator has an initial own stake and can receive delegated stakes from investors.
- **Investors**: Entities that delegate their stakes to validators to earn a share of the rewards.
- **Stake Delegation**: Investors choose validators to delegate their stakes based on expected returns. After each transaction, investors may reallocate their stakes to optimize returns.
- **Transaction Processing**: In each transaction, 5 validators are selected based on their total stakes (own stake + delegated stake). They process the transaction and receive rewards, which are shared between the validators and their investors.
- **Reward Distribution**: Validators keep 10% of the reward, and 90% is distributed among investors who have delegated to them, proportional to their stakes.

Use the controls in the sidebar to adjust parameters like the number of validators and investors, the stakes, the number of transactions, and the reward per transaction. Observe how these changes affect the stake evolution of both validators and investors.
"""
)
